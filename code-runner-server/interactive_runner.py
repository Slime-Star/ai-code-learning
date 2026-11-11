"""Stream a single program's output and keep stdin open for console input.

Popen pipe I/O runs in worker threads so this also works with the Windows
SelectorEventLoop used by uvicorn's reload mode.
"""

import asyncio
import codecs
import contextlib
import io
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile

from anyio import CancelScope
from fastapi import WebSocket, WebSocketDisconnect


SESSION_TIMEOUT = 300
COMPILE_TIMEOUT = 20
MAX_OUTPUT_BYTES = 1024 * 1024
MAX_INPUT_BYTES = 1024 * 1024


def _spawn(command, directory, env):
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    return subprocess.Popen(
        command, cwd=directory, env=env, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0, **options,
    )


def _terminate(process):
    if process is None:
        return
    if os.name == "nt" and process.poll() is None:
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=5, creationflags=subprocess.CREATE_NO_WINDOW,
        )
    elif os.name != "nt":
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
    if process.poll() is None:
        process.kill()
    process.wait(timeout=5)


def _commands(language, code, directory):
    root = Path(directory)
    if language == "python":
        source = root / "main.py"
        source.write_text(code, encoding="utf-8")
        return None, [sys.executable, "-X", "utf8", "-u", str(source)]
    if language == "javascript":
        source = root / "main.js"
        source.write_text(code, encoding="utf-8")
        return None, ["node", str(source)]
    if language == "java":
        match = re.search(r"\bpublic\s+(?:(?:final|abstract)\s+)?class\s+([A-Za-z_$][\w$]*)", code)
        if match is None:
            match = re.search(r"\bclass\s+([A-Za-z_$][\w$]*)", code)
        if match is None:
            raise ValueError("未检测到有效的 Java class 定义")
        name = match.group(1)
        source = root / f"{name}.java"
        source.write_text(code, encoding="utf-8")
        return ["javac", "-encoding", "UTF-8", str(source)], [
            "java", "-Dfile.encoding=UTF-8", "-Dstdin.encoding=UTF-8",
            "-Dstdout.encoding=UTF-8", "-Dstderr.encoding=UTF-8", "-cp", directory, name,
        ]
    if language == "c":
        source = root / "main.c"
        executable = root / ("main.exe" if os.name == "nt" else "main")
        source.write_text(code, encoding="utf-8")
        # A pipe is not a TTY: disable C stdio buffering so prompts before scanf
        # reach the browser even when they do not end in a newline.
        wrapper = root / "console.c"
        wrapper.write_text(
            '#include <stdio.h>\n'
            'static void __attribute__((constructor)) console_init(void) {\n'
            'setvbuf(stdout, NULL, _IONBF, 0); setvbuf(stderr, NULL, _IONBF, 0);\n'
            '}\n', encoding="utf-8",
        )
        return ["gcc", str(source), str(wrapper), "-o", str(executable), "-std=c11", "-O2",
                "-finput-charset=UTF-8", "-fexec-charset=UTF-8"], [str(executable)]
    raise ValueError(f"暂不支持 {language} 语言")


async def run_console(websocket: WebSocket, record_submission=None):
    await websocket.accept()
    process = None
    tasks = []
    request = None
    result = None
    inputs = []
    outputs = []
    output_bytes = 0
    input_bytes = 0
    stdin_finished = False
    input_queue = asyncio.Queue()
    directory = tempfile.TemporaryDirectory(prefix="code_console_")
    send_lock = asyncio.Lock()

    async def send(message):
        async with send_lock:
            await websocket.send_json(message)

    async def pump_output(active_process):
        nonlocal output_bytes
        decoder = io.IncrementalNewlineDecoder(codecs.getincrementaldecoder("utf-8")("replace"), translate=True)
        while True:
            chunk = await asyncio.to_thread(active_process.stdout.read, 4096)
            if not chunk:
                tail = decoder.decode(b"", final=True)
                if tail:
                    outputs.append(tail)
                    await send({"type": "output", "data": tail})
                return
            output_bytes += len(chunk)
            if output_bytes > MAX_OUTPUT_BYTES:
                raise ValueError("输出超过 1 MB，程序已停止")
            text = decoder.decode(chunk)
            if text:
                outputs.append(text)
                await send({"type": "output", "data": text})

    async def receive_input():
        nonlocal input_bytes, stdin_finished
        while True:
            message = await websocket.receive_json()
            if not isinstance(message, dict):
                raise ValueError("无效的控制台消息")
            kind = message.get("type")
            if kind == "stop":
                return "stopped"
            if kind == "eof":
                if process is not None and not process.stdin.closed and not stdin_finished:
                    stdin_finished = True
                    input_queue.put_nowait(None)
                continue
            if kind != "input":
                raise ValueError("无效的控制台操作")
            if process is None or process.poll() is not None or process.stdin.closed or stdin_finished:
                continue
            text = str(message.get("data", "")).replace("\r\n", "\n").replace("\r", "\n")
            encoded = text.encode("utf-8")
            input_bytes += len(encoded)
            if input_bytes > MAX_INPUT_BYTES:
                raise ValueError("输入超过 1 MB，程序已停止")
            # Echo before writing, so the program's response follows the input.
            await send({"type": "input", "data": text})
            inputs.append(text)
            input_queue.put_nowait(encoded)

    async def pump_input():
        # Keep receiving stop/disconnect while a large paste is blocked writing
        # to a program that is not reading stdin.
        while True:
            encoded = await input_queue.get()
            try:
                if encoded is None:
                    await asyncio.to_thread(process.stdin.close)
                    await send({"type": "stdin_closed"})
                    return
                def write_all():
                    remaining = memoryview(encoded)
                    while remaining:
                        count = process.stdin.write(remaining)
                        if not count:
                            raise BrokenPipeError("程序输入已关闭")
                        remaining = remaining[count:]
                await asyncio.to_thread(write_all)
            except (BrokenPipeError, OSError):
                return  # Program may exit immediately after its last read.

    async def wait_for_phase(pump, waiter, receiver):
        pending = {pump, receiver, waiter}
        while waiter in pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                value = task.result()
                if task is receiver and value == "stopped":
                    return False
        await pump
        return True

    async def execute():
        nonlocal process, request
        request = await websocket.receive_json()
        if not isinstance(request, dict) or request.get("type") != "start":
            raise ValueError("请先启动程序")
        language = str(request.get("lang", ""))
        code = str(request.get("code", ""))
        if not code.strip():
            raise ValueError("请先输入代码")
        if len(code) > 100000:
            raise ValueError("代码长度超过限制（最大100000字符）")
        compile_command, run_command = _commands(language, code, directory.name)
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONUNBUFFERED="1")
        receiver = asyncio.create_task(receive_input())
        tasks.append(receiver)
        # Keep creation synchronous: cancellation must never leave an untracked
        # child process that was still being created by a worker thread.
        if compile_command:
            await send({"type": "status", "data": "正在编译"})
            process = _spawn(compile_command, directory.name, env)
            process.stdin.close()
            pump = asyncio.create_task(pump_output(process))
            waiter = asyncio.create_task(asyncio.to_thread(process.wait))
            tasks.extend([pump, waiter])
            finished = await asyncio.wait_for(wait_for_phase(pump, waiter, receiver), timeout=COMPILE_TIMEOUT)
            if not finished:
                return {"success": False, "cancelled": True, "error": "程序已停止"}
            exit_code = process.returncode
            if exit_code:
                return {"success": False, "output": "".join(outputs), "error": "".join(outputs) or "编译失败", "exit_code": exit_code}
            process.stdout.close()
        process = _spawn(run_command, directory.name, env)
        writer = asyncio.create_task(pump_input())
        tasks.append(writer)
        await send({"type": "started"})
        pump = asyncio.create_task(pump_output(process))
        waiter = asyncio.create_task(asyncio.to_thread(process.wait))
        tasks.extend([pump, waiter])
        # Keep the output reader in the wait set to surface output limits even
        # when an infinite loop is producing output without exiting.
        if not await wait_for_phase(pump, waiter, receiver):
            return {"success": False, "cancelled": True, "error": "程序已停止"}
        return {
            "success": process.returncode == 0,
            "output": "".join(outputs),
            "error": "" if process.returncode == 0 else ("".join(outputs) or f"程序退出，代码 {process.returncode}"),
            "exit_code": process.returncode,
        }

    try:
        result = await asyncio.wait_for(execute(), timeout=SESSION_TIMEOUT)
    except WebSocketDisconnect:
        pass
    except asyncio.TimeoutError:
        result = {"success": False, "error": "运行超时，程序已停止（单次控制台最多运行5分钟，编译最多20秒）"}
    except FileNotFoundError as exc:
        result = {"success": False, "error": f"未找到运行环境：{exc.filename}，请检查对应语言是否已安装并加入 PATH"}
    except Exception as exc:
        result = {"success": False, "error": str(exc) or "控制台运行失败"}
    finally:
        # ASGI servers can cancel the connection scope on disconnect. Shield
        # cleanup so the child and pipe handles are still released in that case.
        with CancelScope(shield=True):
            # Terminate before cancelling readers to release their pipe reads.
            if process is not None:
                with contextlib.suppress(Exception):
                    await asyncio.to_thread(_terminate, process)
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if process is not None:
                for pipe in (process.stdin, process.stdout):
                    if pipe:
                        with contextlib.suppress(Exception):
                            pipe.close()
            with contextlib.suppress(OSError):
                directory.cleanup()
            if result is not None:
                result.setdefault("output", "".join(outputs))
                result["input"] = "".join(inputs)
                if record_submission and request and not result.get("cancelled"):
                    with contextlib.suppress(Exception):
                        submission_id = await asyncio.to_thread(record_submission, request, result)
                        if submission_id is not None:
                            result["submission_id"] = submission_id
                with contextlib.suppress(Exception):
                    await send({"type": "exit", **result})
            with contextlib.suppress(Exception):
                await websocket.close()
