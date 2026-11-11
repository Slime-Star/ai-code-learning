
import asyncio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware
import subprocess
import tempfile
import uvicorn
import re
import time
import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from pydantic import BaseModel, Field
import sqlite3
from datetime import datetime, timedelta
import hashlib
import secrets
from fastapi import Header
import httpx
from interactive_runner import run_console
from content_api import initialize_content, create_content_router
from learning_analysis import create_analysis_router, deepseek_model



# ====================== FastAPI 初始化及跨域配置 ======================
app = FastAPI(redirect_slashes=False)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=700)

_UPLOAD_ROOT = Path(__file__).resolve().parent / "uploads"
try:
    _UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
app.mount("/api/uploads", StaticFiles(directory=str(_UPLOAD_ROOT)), name="uploads")

def load_env_file():
    try:
        env_path = Path(__file__).resolve().parent / ".env"
        if not env_path.exists():
            return
        raw = env_path.read_bytes()
        raw_no_nul = raw.replace(b"\x00", b"")
        text = ""
        for enc in ("utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "utf-8", "gbk", "latin1"):
            try:
                text = raw_no_nul.decode(enc)
                if "=" in text:
                    break
            except Exception:
                continue
        if not text:
            return
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if not key:
                continue
            existed = os.environ.get(key)
            if existed is None or str(existed).strip() == "":
                os.environ[key] = value
    except Exception:
        return

load_env_file()

# ====================== 判题配置 + 接口 ======================
JUDGE0_URL = "http://150.158.24.107:2358"

LANG_ID = {
    "python": 71,
    "c": 75,
    "java": 13,
    "javascript": 63
}

class CodeRequest(BaseModel):
    code: str
    lang: str
    stdin: str = ""

@app.post("/api/judge")
async def judge_code(req: CodeRequest):
    if req.lang not in LANG_ID:
        raise HTTPException(status_code=400, detail="不支持的语言")

    lid = LANG_ID[req.lang]

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # 1. 提交代码到 Judge0
            resp = await client.post(
                f"{JUDGE0_URL}/submissions?base64_encoded=false",
                json={
                    "source_code": req.code,
                    "language_id": lid,
                    "stdin": req.stdin,
                    "cpu_time_limit": 1,
                    "memory_limit": 65536
                }
            )
            
            # 检查提交是否成功
            if resp.status_code != 201:
                raise Exception(f"Judge0 提交失败，状态码: {resp.status_code}, 响应内容: {resp.text}")
            
            # 解析返回的 token
            try:
                resp_data = resp.json()
            except Exception as e:
                raise Exception(f"Judge0 返回的不是有效的 JSON: {resp.text}") from e
            
            token = resp_data.get("token")
            if not token:
                raise Exception("Judge0 没有返回 token")

            # 2. 轮询判题结果
            result = None
            for i in range(20):
                await asyncio.sleep(0.5)
                r = await client.get(f"{JUDGE0_URL}/submissions/{token}", timeout=5)
                if r.status_code != 200:
                    continue
                
                try:
                    result = r.json()
                except Exception:
                    continue

                if result.get("status", {}).get("id", 0) >= 3:
                    break

            if not result:
                raise Exception("判题超时，没有获取到结果")

            # 3. 构造返回数据
            return {
                "status": result["status"]["description"],
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "time": result.get("time", "0"),
                "memory": result.get("memory", "0")
            }

    except httpx.ConnectError:
        raise HTTPException(status_code=500, detail="无法连接到 Judge0，请检查服务器状态")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"错误详情: {str(e)}")
# ====================== 判题代码结束 ======================

DB_PATH = Path(__file__).resolve().parent / "code_platform.db"
_USER_SEARCH_CACHE = {}
_USER_SEARCH_CACHE_TTL_SEC = 8
_UNREAD_COUNT_CACHE = {}
_CONVERSATIONS_CACHE = {}
_MESSAGES_CACHE_TTL_SEC = 15
_ASYNC_LOCKS = {}

def _get_async_lock(name: str, uid: str):
    k = f"{str(name or '').strip()}:{str(uid or '').strip()}"
    lock = _ASYNC_LOCKS.get(k)
    if lock is None:
        lock = asyncio.Lock()
        _ASYNC_LOCKS[k] = lock
    return lock

def _db_connect():
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    try:
        conn.execute("PRAGMA busy_timeout=30000;")
    except Exception:
        pass
    mode = str(os.environ.get("SQLITE_JOURNAL_MODE") or "TRUNCATE").strip().upper()
    if mode not in ("WAL", "DELETE", "TRUNCATE", "PERSIST", "MEMORY", "OFF"):
        mode = "TRUNCATE"
    try:
        conn.execute(f"PRAGMA journal_mode={mode};")
    except Exception:
        pass
    conn.execute("PRAGMA synchronous=NORMAL;")
    try:
        conn.execute("PRAGMA temp_store=MEMORY;")
    except Exception:
        pass
    if mode == "WAL":
        try:
            conn.execute("PRAGMA wal_autocheckpoint=2000;")
        except Exception:
            pass
    return conn

def _conv_id_class(class_id: str) -> str:
    return f"conv_{str(class_id or '').strip()}"

def _conv_id_dm(a: str, b: str) -> str:
    a1 = str(a or '').strip()
    b1 = str(b or '').strip()
    pair = sorted([a1, b1])
    return f"dm_{pair[0]}_{pair[1]}"

def _ensure_class_group(cur, class_id: str, class_name: str, teacher_id: str):
    cid = _conv_id_class(class_id)
    title = f"{str(class_name or '').strip()} 班级群"
    cur.execute(
        "INSERT OR IGNORE INTO conversations (id, type, title, class_id) VALUES (?, 'class', ?, ?)",
        (cid, title, str(class_id or '').strip())
    )
    tid = str(teacher_id or '').strip()
    if tid:
        cur.execute(
            "INSERT OR IGNORE INTO conversation_members (conversation_id, user_id, last_read_at, last_read_id) "
            "VALUES (?, ?, CURRENT_TIMESTAMP, (SELECT IFNULL(MAX(id), 0) FROM messages WHERE conversation_id = ?))",
            (cid, tid, cid)
        )
    return cid

def init_database():
    conn = _db_connect()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
    goods_initialized = cursor.execute("SELECT 1 FROM app_settings WHERE key='seed_v1:goods'").fetchone() is not None
    competitions_initialized = cursor.execute("SELECT 1 FROM app_settings WHERE key='seed_v1:competitions'").fetchone() is not None
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS code_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            student_name TEXT DEFAULT '游客',
            problem_id TEXT NOT NULL,
            code TEXT NOT NULL,
            language TEXT NOT NULL,
            input_data TEXT,
            output TEXT,
            error TEXT,
            success BOOLEAN,
            exercise_metadata TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_student ON code_submissions(student_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_problem ON code_submissions(problem_id)')
    submission_columns = {row[1] for row in cursor.execute('PRAGMA table_info(code_submissions)')}
    if 'exercise_metadata' not in submission_columns:
        cursor.execute("ALTER TABLE code_submissions ADD COLUMN exercise_metadata TEXT DEFAULT '{}'")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL DEFAULT 'student',
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            email TEXT,
            name TEXT,
            avatar TEXT,
            collected_courses TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_name ON users(name)')
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role_username ON users(role, username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role_name ON users(role, name)")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_state (
            user_id TEXT PRIMARY KEY,
            daily_checkin TEXT,
            practice_done TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id TEXT PRIMARY KEY,
            teacher_id TEXT NOT NULL,
            name TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_classes_teacher ON classes(teacher_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS class_members (
            class_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (class_id, student_id)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_class_members_student ON class_members(student_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            title TEXT,
            class_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_type ON conversations(type)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_members (
            conversation_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_read_at TIMESTAMP,
            PRIMARY KEY (conversation_id, user_id)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_conv_members_user ON conversation_members(user_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            sender_id TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conv_id ON messages(conversation_id, id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS friend_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id TEXT NOT NULL,
            to_user_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_friend_requests_to ON friend_requests(to_user_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS friends (
            user_id TEXT NOT NULL,
            friend_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, friend_id)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_friends_user ON friends(user_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkin_tasks (
            id TEXT PRIMARY KEY,
            teacher_id TEXT NOT NULL,
            class_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            language TEXT NOT NULL,
            starter_code TEXT,
            expected_output TEXT,
            solution_code TEXT,
            due_at TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_class ON checkin_tasks(class_id)')

    # 测试表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT,
            name TEXT NOT NULL,
            desc TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'algorithm',
            mode TEXT NOT NULL DEFAULT 'general',
            status TEXT NOT NULL DEFAULT 'registering',
            difficulty TEXT NOT NULL DEFAULT '中等',
            participants INTEGER NOT NULL DEFAULT 0,
            duration TEXT NOT NULL DEFAULT '4小时',
            register_time TEXT,
            competition_time TEXT,
            tags TEXT,
            detail_desc TEXT,
            rules TEXT,
            rewards TEXT,
            ended_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_competitions_status ON competitions(status)')
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_competitions_teacher ON competitions(teacher_id)')
    except Exception:
        pass

    # 测试报名表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competition_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_id INTEGER NOT NULL,
            competition_name TEXT NOT NULL,
            user_id TEXT NOT NULL,
            user_name TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(competition_id, user_id)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_registrations_competition ON competition_registrations(competition_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_registrations_user ON competition_registrations(user_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competition_problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_id INTEGER NOT NULL,
            task_id TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '',
            points INTEGER NOT NULL DEFAULT 100,
            sort INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(competition_id, task_id)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_comp_problem_comp ON competition_problems(competition_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_comp_problem_task ON competition_problems(task_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competition_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_id INTEGER NOT NULL,
            task_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            language TEXT NOT NULL,
            code TEXT NOT NULL,
            input_data TEXT,
            output TEXT,
            error TEXT,
            passed INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(competition_id, task_id, user_id)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_comp_sub_user ON competition_submissions(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_comp_sub_comp ON competition_submissions(competition_id)')

    # 积分商品表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS points_goods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            desc TEXT,
            image TEXT,
            points INTEGER NOT NULL DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 0,
            category TEXT NOT NULL DEFAULT 'stationery',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_goods_category ON points_goods(category)')

    # 兑换记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exchange_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            goods_id INTEGER NOT NULL,
            goods_name TEXT NOT NULL,
            goods_image TEXT,
            points INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_exchange_user ON exchange_records(user_id)')

    # 积分流水表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS points_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            change INTEGER NOT NULL DEFAULT 0,
            type TEXT NOT NULL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_points_user ON points_logs(user_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS solution_unlocks (
            user_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            key TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, kind, key)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_solution_unlocks_user ON solution_unlocks(user_id)')

    # 每日签到表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_signin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            signin_date TEXT NOT NULL,
            consecutive_days INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, signin_date)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_signin_user ON daily_signin(user_id)')

    # 给积分商品表插入一些默认数据
    cursor.execute('SELECT COUNT(*) FROM points_goods')
    if cursor.fetchone()[0] == 0 and not goods_initialized:
        default_goods = [
            ('精美书签', '金属质感书签，阅读好伴侣', 'https://picsum.photos/200/200?random=1', 100, 100, 'stationery'),
            ('定制笔记本', '精美定制笔记本，记录学习点滴', 'https://picsum.photos/200/200?random=2', 500, 30, 'stationery'),
            ('钢笔套装', '高品质钢笔，书写流畅顺滑', 'https://picsum.photos/200/200?random=3', 800, 20, 'stationery'),
            ('精美帆布袋', '环保耐用的定制帆布袋', 'https://picsum.photos/200/200?random=4', 300, 50, 'stationery'),
            ('鼠标垫', '超大号游戏鼠标垫，编程更舒适', 'https://picsum.photos/200/200?random=5', 400, 25, 'digital'),
            ('编程书籍', '精选编程书籍，提升技术水平', 'https://picsum.photos/200/200?random=6', 1200, 15, 'books'),
            ('USB充电宝', '10000mAh便携充电宝', 'https://picsum.photos/200/200?random=7', 1500, 10, 'digital'),
            ('学习课程月卡', '解锁全部精品课程', 'https://picsum.photos/200/200?random=8', 2000, 999, 'virtual')
        ]
        for goods in default_goods:
            cursor.execute('INSERT INTO points_goods (name, desc, image, points, stock, category) VALUES (?, ?, ?, ?, ?, ?)', goods)

    # 给测试表插入一些默认数据（如果没有的话）
    cursor.execute('SELECT COUNT(*) FROM competitions')
    if cursor.fetchone()[0] == 0 and not competitions_initialized:
        default_competitions = [
            ('2026全国大学生程序设计大赛', '面向全国大学生的算法测试，考察数据结构与算法能力！', 'algorithm', 'registering', '中等', 1256, '4小时', '05-01 ~ 05-30', '06-10 09:00 ~ 13:00', '算法,数据结构,大学生,ACM', '本次测试旨在培养和提高大学生的程序设计与算法分析能力，测试题目涵盖数组、链表、树、图等数据结构。', '比赛时长为4小时，共8道题目,可以使用C++、Java、Python、JavaScript四种语言,禁止使用任何网络资源', '一等奖：5名，奖金5000元 + 荣誉证书,二等奖：10名，奖金3000元 + 荣誉证书,三等奖：20名，奖金1000元 + 荣誉证书'),
            ('Web应用开发挑战赛', '以实际项目为导向的Web开发测试，48小时内完成一个功能完整的应用！', 'web', 'ongoing', '较难', 892, '48小时', '04-15 ~ 05-15', '05-20 00:00 ~ 05-22 00:00', 'Web开发,前端,后端,全栈', '本次测试要求选手在48小时内完成一个功能完整、设计美观的Web应用，包含用户系统、数据管理、界面设计等多个模块。', '比赛时长为48小时,前端框架不限，推荐使用Vue或React,后端语言不限，可使用Node.js、Python、Java等,需要提交完整的代码、部署说明与演示链接,允许使用开源库但需在文档中注明来源,禁止抄袭与恶意刷榜', '最佳应用奖：1名，奖金8000元 + 荣誉证书,最佳设计奖：1名，奖金5000元 + 荣誉证书,最佳创新奖：1名，奖金5000元 + 荣誉证书'),
            ('Python数据科学测试', '数据处理与分析测试，考察数据分析、机器学习、可视化等能力！', 'data', 'registering', '中等', 567, '72小时', '05-10 ~ 06-10', '06-15 00:00 ~ 06-18 00:00', 'Python,数据科学,机器学习', '本次测试围绕真实数据集展开，选手需要完成数据清洗、特征工程、模型训练、结果可视化等完整流程。', '比赛时长72小时,使用Python语言完成数据处理与分析,允许使用numpy、pandas、scikit-learn等常用库,需提交可复现的代码（Notebook/脚本）与简要报告,不得伪造数据或抄袭他人成果', '一等奖：1名，奖金6000元 + 荣誉证书,二等奖：3名，奖金3000元 + 荣誉证书,三等奖：5名，奖金1500元 + 荣誉证书')
        ]
        for comp in default_competitions:
            cursor.execute('''
                INSERT INTO competitions (name, desc, type, status, difficulty, participants, duration, register_time, competition_time, tags, detail_desc, rules, rewards)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', comp)
    elif not competitions_initialized:
        try:
            cursor.execute(
                "UPDATE competitions SET detail_desc = ?, rules = ?, rewards = ?, tags = ? "
                "WHERE name = ? AND (detail_desc IS NULL OR detail_desc = '' OR rules IS NULL OR rules = '' OR rewards IS NULL OR rewards = '' OR tags IS NULL OR tags = '')",
                (
                    '本次测试要求选手在48小时内完成一个功能完整、设计美观的Web应用，包含用户系统、数据管理、界面设计等多个模块。',
                    '比赛时长为48小时,前端框架不限，推荐使用Vue或React,后端语言不限，可使用Node.js、Python、Java等,需要提交完整的代码、部署说明与演示链接,允许使用开源库但需在文档中注明来源,禁止抄袭与恶意刷榜',
                    '最佳应用奖：1名，奖金8000元 + 荣誉证书,最佳设计奖：1名，奖金5000元 + 荣誉证书,最佳创新奖：1名，奖金5000元 + 荣誉证书',
                    'Web开发,前端,后端,全栈',
                    'Web应用开发挑战赛',
                ),
            )
            cursor.execute(
                "UPDATE competitions SET detail_desc = ?, rules = ?, rewards = ?, tags = ? "
                "WHERE name = ? AND (detail_desc IS NULL OR detail_desc = '' OR rules IS NULL OR rules = '' OR rewards IS NULL OR rewards = '' OR tags IS NULL OR tags = '')",
                (
                    '本次测试围绕真实数据集展开，选手需要完成数据清洗、特征工程、模型训练、结果可视化等完整流程。',
                    '比赛时长72小时,使用Python语言完成数据处理与分析,允许使用numpy、pandas、scikit-learn等常用库,需提交可复现的代码（Notebook/脚本）与简要报告,不得伪造数据或抄袭他人成果',
                    '一等奖：1名，奖金6000元 + 荣誉证书,二等奖：3名，奖金3000元 + 荣誉证书,三等奖：5名，奖金1500元 + 荣誉证书',
                    'Python,数据科学,机器学习',
                    'Python数据科学测试',
                ),
            )
        except Exception:
            pass

    # 兼容旧库：users 表早期版本没有 role 列，这会导致登录 SQL 读取 role 时报错
    user_cols = [r[1] for r in cursor.execute("PRAGMA table_info(users)").fetchall()]
    if "role" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student'")
        # 如果旧数据里已经存在班级/任务记录，则相应用户应为 teacher
        cursor.execute(
            "UPDATE users SET role = 'teacher' "
            "WHERE id IN (SELECT DISTINCT teacher_id FROM classes) "
            "   OR id IN (SELECT DISTINCT teacher_id FROM checkin_tasks)"
        )

    conv_member_cols = [r[1] for r in cursor.execute("PRAGMA table_info(conversation_members)").fetchall()]
    if "last_read_id" not in conv_member_cols:
        try:
            cursor.execute("ALTER TABLE conversation_members ADD COLUMN last_read_id INTEGER DEFAULT 0")
        except Exception:
            pass
    try:
        cursor.execute(
            "UPDATE conversation_members "
            "SET last_read_id = (SELECT IFNULL(MAX(id), 0) FROM messages m WHERE m.conversation_id = conversation_members.conversation_id) "
            "WHERE last_read_at IS NOT NULL AND (last_read_id IS NULL OR last_read_id = 0)"
        )
    except Exception:
        pass

    comp_cols = [r[1] for r in cursor.execute("PRAGMA table_info(competitions)").fetchall()]
    if "mode" not in comp_cols:
        try:
            cursor.execute("ALTER TABLE competitions ADD COLUMN mode TEXT NOT NULL DEFAULT 'general'")
        except Exception:
            pass
    if "teacher_id" not in comp_cols:
        try:
            cursor.execute("ALTER TABLE competitions ADD COLUMN teacher_id TEXT")
        except Exception:
            pass
    try:
        if "teacher_id" in [r[1] for r in cursor.execute("PRAGMA table_info(competitions)").fetchall()]:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_competitions_teacher ON competitions(teacher_id)')
    except Exception:
        pass
    if "ended_at" not in comp_cols:
        try:
            cursor.execute("ALTER TABLE competitions ADD COLUMN ended_at TIMESTAMP")
        except Exception:
            pass

    sub_cols = [r[1] for r in cursor.execute("PRAGMA table_info(competition_submissions)").fetchall()]
    if "score" not in sub_cols:
        try:
            cursor.execute("ALTER TABLE competition_submissions ADD COLUMN score INTEGER")
        except Exception:
            pass
    if "feedback" not in sub_cols:
        try:
            cursor.execute("ALTER TABLE competition_submissions ADD COLUMN feedback TEXT")
        except Exception:
            pass
    if "graded_by" not in sub_cols:
        try:
            cursor.execute("ALTER TABLE competition_submissions ADD COLUMN graded_by TEXT")
        except Exception:
            pass
    if "graded_at" not in sub_cols:
        try:
            cursor.execute("ALTER TABLE competition_submissions ADD COLUMN graded_at TIMESTAMP")
        except Exception:
            pass

    cursor.execute("INSERT OR IGNORE INTO app_settings(key,value) VALUES ('seed_v1:goods','1')")
    cursor.execute("INSERT OR IGNORE INTO app_settings(key,value) VALUES ('seed_v1:competitions','1')")
    initialize_content(conn)
    conn.commit()
    conn.close()

init_database()

# ====================== Python 语言服务器 WebSocket 逻辑 ======================
@app.websocket("/api/ws/python")
async def lsp_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # 启动 Pylsp 进程
    pylsp_process = await asyncio.create_subprocess_exec(
        sys.executable, '-m', 'pylsp',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    async def forward_to_pylsp(pylsp_stdin):
        while True:
            try:
                message = await websocket.receive_text()
                pylsp_stdin.write(message.encode())
                await pylsp_stdin.drain()
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"Error receiving from client: {e}")
                break

    async def forward_to_client(pylsp_stdout):
        while True:
            try:
                line = await pylsp_stdout.readline()
                if not line:
                    break
                await websocket.send_text(line.decode())
            except Exception as e:
                print(f"Error sending to client: {e}")
                break

    # 创建任务来处理双向通信
    stdin_task = asyncio.create_task(forward_to_pylsp(pylsp_process.stdin))
    stdout_task = asyncio.create_task(forward_to_client(pylsp_process.stdout))

    # 等待任务完成
    await asyncio.gather(stdin_task, stdout_task)

    # 清理
    if pylsp_process.returncode is None:
        pylsp_process.kill()
        await pylsp_process.wait()

# ====================== 请求模型 ======================
class CodeRequest(BaseModel):
    student_id: str = "guest"
    student_name: str = "游客"
    problem_id: str = "unknown"
    lang: str
    code: str
    input: str = ""
    exercise: dict = Field(default_factory=dict)

class PracticeResultRequest(BaseModel):
    submission_id: int

class AnalyzeRequest(BaseModel):
    stats: dict

class ChatRequest(BaseModel):
    message: str
    context: dict = Field(default_factory=dict)
    history: list = Field(default_factory=list)

class AutoReviewRequest(BaseModel):
    language: str = ""
    code: str = ""
    error: str = ""
    input: str = ""
    expected_output: str = ""

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str = ""
    role: str = "student"

class LoginRequest(BaseModel):
    username: str
    password: str

class ResetPasswordRequest(BaseModel):
    username: str
    new_password: str

class UpdateProfileRequest(BaseModel):
    name: str = ""
    avatar: str = ""
    collected_courses: list | None = None

class UpdateUserStateRequest(BaseModel):
    daily_checkin: dict = {}
    practice_done: dict = {}

class CreateClassRequest(BaseModel):
    name: str

class JoinClassRequest(BaseModel):
    code: str

class CreateTaskRequest(BaseModel):
    class_id: str
    title: str
    description: str = ""
    language: str
    starter_code: str = ""
    expected_output: str = ""
    solution_code: str = ""
    due_at: str = ""

class LeaveClassRequest(BaseModel):
    class_id: str

class DissolveClassRequest(BaseModel):
    class_id: str

# 测试相关模型
class CompetitionRegisterRequest(BaseModel):
    competition_id: int = Field(..., alias="competitionId")
    competition_name: str = Field("", alias="competitionName")
    user_id: str = Field("", alias="userId")
    user_name: str = Field("", alias="userName")

    class Config:
        allow_population_by_field_name = True

class PublishCompetitionProblemItem(BaseModel):
    task_id: str
    category: str = ""
    points: int = 100
    sort: int = 0

class PublishCompetitionRequest(BaseModel):
    name: str
    desc: str
    type: str = "algorithm"
    mode: str = "general"
    status: str = "registering"
    difficulty: str = "中等"
    duration: str = "4小时"
    register_time: str = ""
    competition_time: str = ""
    tags: str = ""
    detail_desc: str = ""
    rules: str = ""
    rewards: str = ""
    problems: list = []

class CompetitionSubmitRequest(BaseModel):
    task_id: str
    language: str = ""
    code: str
    input_data: str = ""

class CompetitionGradeRequest(BaseModel):
    task_id: str
    user_id: str
    score: int = 0
    feedback: str = ""

# 示例测试数据（用于初始化）
def _init_sample_competitions():
    conn = _db_connect()
    cur = conn.cursor()
    if cur.execute("SELECT 1 FROM app_settings WHERE key='seed_v1:competitions'").fetchone():
        conn.close()
        return
    
    # 检查是否已有数据
    cur.execute("SELECT COUNT(*) FROM competitions")
    count = cur.fetchone()[0]
    
    if count == 0:
        sample_competitions = [
            {
                "name": "2026全国大学生程序设计大赛",
                "desc": "面向全国大学生的算法测试，考察数据结构与算法能力，题目难度适中！",
                "type": "algorithm",
                "status": "registering",
                "difficulty": "中等",
                "participants": 1256,
                "duration": "4小时",
                "register_time": "05-01 ~ 05-30",
                "competition_time": "06-10 09:00 ~ 13:00",
                "tags": json.dumps(["算法", "数据结构", "大学生", "ACM"], ensure_ascii=False),
                "detail_desc": "本次测试旨在培养和提高大学生的程序设计与算法分析能力，测试题目涵盖数组、链表、树、图等数据结构以及排序、搜索、动态规划等算法。",
                "rules": json.dumps([
                    "比赛时长为4小时，共8道题目",
                    "可以使用C++、Java、Python、JavaScript四种语言",
                    "每道题根据通过时间和提交次数计算得分",
                    "禁止使用任何网络资源和第三方库"
                ], ensure_ascii=False),
                "rewards": json.dumps([
                    "一等奖：5名，奖金5000元 + 荣誉证书",
                    "二等奖：10名，奖金3000元 + 荣誉证书",
                    "三等奖：20名，奖金1000元 + 荣誉证书"
                ], ensure_ascii=False)
            },
            {
                "name": "Web应用开发挑战赛",
                "desc": "以实际项目为导向的Web开发测试，48小时内完成一个功能完整的应用！",
                "type": "web",
                "status": "ongoing",
                "difficulty": "较难",
                "participants": 892,
                "duration": "48小时",
                "register_time": "04-15 ~ 05-15",
                "competition_time": "05-20 00:00 ~ 05-22 00:00",
                "tags": json.dumps(["Web开发", "前端", "后端", "全栈"], ensure_ascii=False),
                "detail_desc": "本次测试要求选手在48小时内完成一个功能完整、设计美观的Web应用，包含用户系统、数据管理、界面设计等多个模块。",
                "rules": json.dumps([
                    "比赛时长为48小时",
                    "前端框架不限，推荐使用Vue或React",
                    "后端语言不限，可使用Node.js、Python、Java等",
                    "需要提交完整的代码和演示文档"
                ], ensure_ascii=False),
                "rewards": json.dumps([
                    "最佳应用奖：1名，奖金8000元",
                    "最佳设计奖：1名，奖金5000元",
                    "最佳创新奖：1名，奖金5000元"
                ], ensure_ascii=False)
            },
            {
                "name": "Python数据科学测试",
                "desc": "数据处理与分析测试，考察数据分析、机器学习、可视化等能力！",
                "type": "data",
                "status": "registering",
                "difficulty": "中等",
                "participants": 567,
                "duration": "72小时",
                "register_time": "05-10 ~ 06-10",
                "competition_time": "06-15 00:00 ~ 06-18 00:00",
                "tags": json.dumps(["Python", "数据科学", "机器学习"], ensure_ascii=False),
                "detail_desc": "本次测试围绕真实数据集展开，选手需要完成数据清洗、特征工程、模型训练、结果可视化等完整流程。",
                "rules": json.dumps([
                    "比赛时长72小时",
                    "使用Python语言，可使用numpy、pandas等库",
                    "需要提交完整的分析报告和代码"
                ], ensure_ascii=False),
                "rewards": json.dumps([
                    "一等奖：1名，奖金6000元",
                    "二等奖：3名，奖金3000元",
                    "三等奖：5名，奖金1500元"
                ], ensure_ascii=False)
            }
        ]
        
        for comp in sample_competitions:
            cur.execute('''
                INSERT INTO competitions 
                (name, desc, type, status, difficulty, participants, duration, 
                 register_time, competition_time, tags, detail_desc, rules, rewards)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                comp["name"], comp["desc"], comp["type"], comp["status"],
                comp["difficulty"], comp["participants"], comp["duration"],
                comp["register_time"], comp["competition_time"],
                comp["tags"], comp["detail_desc"], comp["rules"], comp["rewards"]
            ))
        
        conn.commit()
    
    conn.close()

def _hash_password(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
    return dk.hex()

def _create_user(username: str, password: str, email: str, role: str):
    role = role if role in ("student", "teacher") else "student"
    prefix = "tch" if role == "teacher" else "stu"
    user_id = f"{prefix}_{secrets.token_hex(8)}"
    salt_hex = secrets.token_hex(16)
    password_hash = _hash_password(password, salt_hex)
    avatar = f"https://picsum.photos/seed/{username}/100/100"
    name = username
    collected_courses = "[]"

    conn = _db_connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (id, username, role, password_hash, salt, email, name, avatar, collected_courses) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, username, role, password_hash, salt_hex, email or "", name, avatar, collected_courses)
    )
    conn.commit()
    conn.close()
    return {"id": user_id, "username": username, "role": role, "name": name, "avatar": avatar, "collectedCourses": []}

def _issue_token(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    expires_dt = datetime.utcfromtimestamp(datetime.utcnow().timestamp() + 7 * 24 * 3600).isoformat(timespec="seconds")
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)", (token, user_id, expires_dt))
    conn.commit()
    conn.close()
    return token

def _get_user_by_id(user_id: str):
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, username, role, name, avatar, collected_courses FROM users WHERE id = ? LIMIT 1", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    role = row["role"] or "student"
    # 兼容旧数据：如果历史上创建过班级/发布过任务，但 role 被默认成 student，则自动修正为 teacher
    if role == "student":
        try:
            conn2 = _db_connect()
            cur2 = conn2.cursor()
            cur2.execute("SELECT 1 FROM classes WHERE teacher_id = ? LIMIT 1", (user_id,))
            has_class = cur2.fetchone() is not None
            has_task = False
            if not has_class:
                cur2.execute("SELECT 1 FROM checkin_tasks WHERE teacher_id = ? LIMIT 1", (user_id,))
                has_task = cur2.fetchone() is not None
            if has_class or has_task:
                cur2.execute("UPDATE users SET role = 'teacher' WHERE id = ?", (user_id,))
                conn2.commit()
                role = "teacher"
            conn2.close()
        except Exception:
            pass
    try:
        courses = json.loads(row["collected_courses"] or "[]")
        if not isinstance(courses, list):
            courses = []
    except Exception:
        courses = []
    return {
        "id": row["id"],
        "username": row["username"],
        "role": role,
        "name": row["name"] or row["username"],
        "avatar": row["avatar"] or "",
        "collectedCourses": courses
    }

def _require_user(authorization: str = Header(None)):
    if not authorization or not str(authorization).lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = str(authorization)[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT user_id, expires_at FROM sessions WHERE token = ? LIMIT 1", (token,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="登录已失效")
    try:
        expires = datetime.fromisoformat(row["expires_at"])
    except Exception:
        raise HTTPException(status_code=401, detail="登录已失效")
    if expires < datetime.utcnow():
        raise HTTPException(status_code=401, detail="登录已过期")
    user = _get_user_by_id(row["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user

def _require_teacher(user: dict):
    if (user or {}).get("role") != "teacher":
        raise HTTPException(status_code=403, detail="需要教师权限")

def _require_student(user: dict):
    if (user or {}).get("role") != "student":
        raise HTTPException(status_code=403, detail="需要学生权限")

def _get_user_state(user_id: str):
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT daily_checkin, practice_done FROM user_state WHERE user_id = ? LIMIT 1", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"daily_checkin": {}, "practice_done": {}}
    try:
        daily_checkin = json.loads(row["daily_checkin"] or "{}")
        if not isinstance(daily_checkin, dict):
            daily_checkin = {}
    except Exception:
        daily_checkin = {}
    try:
        practice_done = json.loads(row["practice_done"] or "{}")
        if not isinstance(practice_done, dict):
            practice_done = {}
    except Exception:
        practice_done = {}
    return {"daily_checkin": daily_checkin, "practice_done": practice_done}

def _upsert_user_state(user_id: str, daily_checkin: dict, practice_done: dict):
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_state (user_id, daily_checkin, practice_done, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP) "
        "ON CONFLICT(user_id) DO UPDATE SET daily_checkin=excluded.daily_checkin, practice_done=excluded.practice_done, updated_at=CURRENT_TIMESTAMP",
        (user_id, json.dumps(daily_checkin or {}, ensure_ascii=False), json.dumps(practice_done or {}, ensure_ascii=False))
    )
    conn.commit()
    conn.close()

@app.post("/api/auth/register")
async def auth_register(req: RegisterRequest):
    username = str(req.username or "").strip()
    password = str(req.password or "")
    email = str(req.email or "").strip()
    role = str(req.role or "student").strip().lower()
    if len(username) < 3 or len(username) > 20:
        raise HTTPException(status_code=400, detail="用户名长度需为 3-20 位")
    if len(password) < 6 or len(password) > 20:
        raise HTTPException(status_code=400, detail="密码长度需为 6-20 位")
    if role not in ("student", "teacher"):
        raise HTTPException(status_code=400, detail="角色不合法")

    conn = _db_connect()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1", (username,))
    existed = cur.fetchone()
    conn.close()
    if existed:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = _create_user(username, password, email, role)
    return {"success": True, "user": user}

@app.post("/api/auth/login")
async def auth_login(req: LoginRequest):
    username = str(req.username or "").strip()
    password = str(req.password or "")
    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名或密码不能为空")
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, username, role, password_hash, salt FROM users WHERE username = ? LIMIT 1", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=400, detail="用户名不存在")
    calc = _hash_password(password, row["salt"])
    if calc != row["password_hash"]:
        raise HTTPException(status_code=400, detail="密码错误")
    token = _issue_token(row["id"])
    user = _get_user_by_id(row["id"])
    return {"success": True, "token": token, "user": user}

@app.get("/api/auth/me")
async def auth_me(authorization: str = Header(None)):
    user = _require_user(authorization)
    return {"success": True, "user": user}

@app.post("/api/auth/reset-password")
async def auth_reset_password(req: ResetPasswordRequest):
    username = str(req.username or "").strip()
    new_password = str(req.new_password or "")
    if len(new_password) < 6 or len(new_password) > 20:
        raise HTTPException(status_code=400, detail="密码长度需为 6-20 位")
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, salt, role FROM users WHERE username = ? LIMIT 1", (username,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail="用户名不存在")
    if row["role"] == "admin":
        conn.close()
        raise HTTPException(status_code=403, detail="管理员密码请通过管理端或本机管理工具重置")
    password_hash = _hash_password(new_password, row["salt"])
    cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, row["id"]))
    conn.commit()
    conn.close()
    return {"success": True}

@app.put("/api/users/me")
async def update_me(req: UpdateProfileRequest, authorization: str = Header(None)):
    user = _require_user(authorization)
    name = str(req.name or "").strip() or user["name"]
    avatar = str(req.avatar or "").strip() or user["avatar"]
    courses = json.dumps(req.collected_courses, ensure_ascii=False) if isinstance(req.collected_courses, list) else None
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET name = ?, avatar = ?, collected_courses = COALESCE(?, collected_courses) WHERE id = ?",
        (name, avatar, courses, user["id"])
    )
    conn.commit()
    conn.close()
    updated = _get_user_by_id(user["id"])
    return {"success": True, "user": updated}

@app.get("/api/users/public/{user_id}")
async def get_public_user(user_id: str):
    uid = str(user_id or "").strip()
    if not uid:
        raise HTTPException(status_code=400, detail="缺少user_id")
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, role, name, avatar, created_at FROM users WHERE id = ? LIMIT 1",
        (uid,)
    )
    u = cur.fetchone()
    if not u or str(u["role"] or "") != "student":
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")

    cur.execute(
        """
        SELECT
          COUNT(*) AS total_runs,
          SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS success_runs,
          COUNT(DISTINCT CASE WHEN success = 1 THEN problem_id ELSE NULL END) AS passed_unique
        FROM code_submissions WHERE student_id = ?
        """,
        (uid,)
    )
    st = cur.fetchone() or {}

    cur.execute(
        "SELECT COALESCE(SUM(change), 0) FROM points_logs WHERE user_id = ?",
        (uid,)
    )
    pts = int(cur.fetchone()[0] or 0)
    if pts < 0:
        pts = 0

    conn.close()
    total_runs = int(st["total_runs"] or 0) if isinstance(st, sqlite3.Row) else int(st[0] or 0)
    success_runs = int(st["success_runs"] or 0) if isinstance(st, sqlite3.Row) else int(st[1] or 0)
    passed_unique = int(st["passed_unique"] or 0) if isinstance(st, sqlite3.Row) else int(st[2] or 0)
    return {
        "success": True,
        "user": {
            "id": str(u["id"]),
            "username": str(u["username"] or ""),
            "name": str(u["name"] or u["username"] or ""),
            "avatar": str(u["avatar"] or ""),
            "created_at": str(u["created_at"] or "")
        },
        "stats": {
            "total_runs": total_runs,
            "success_runs": success_runs,
            "passed_unique": passed_unique
        },
        "points": pts
    }

@app.get("/api/users/search")
async def search_users(q: str = "", limit: int = Query(8), authorization: str = Header(None), x_trace_id: str = Header(None)):
    user = _require_user(authorization)
    _require_student(user)
    t0 = time.perf_counter()
    kw = str(q or "").strip()
    lim = int(limit or 8)
    if lim <= 0:
        lim = 8
    if lim > 10:
        lim = 10
    if len(kw) < 2:
        return {"success": True, "users": []}
    like_prefix = f"{kw}%"

    cache_key = f"{str(user['id'])}:{kw.lower()}:{lim}"
    now_ts = time.time()
    cached = _USER_SEARCH_CACHE.get(cache_key)
    if cached and (now_ts - float(cached.get("ts") or 0)) < _USER_SEARCH_CACHE_TTL_SEC:
        return {"success": True, "users": cached.get("users") or []}

    uid = str(user["id"])

    def _work():
        conn = _db_connect()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rows = []
        try:
            cur.execute(
                "SELECT id, username, COALESCE(name, username, '') AS name, COALESCE(avatar, '') AS avatar "
                "FROM users "
                "WHERE role = 'student' AND id != ? AND (id = ? OR username = ?) "
                "LIMIT 3",
                (uid, kw, kw)
            )
            rows.extend(cur.fetchall() or [])
        except Exception:
            pass

        try:
            remain = max(lim - len(rows), 0)
            if remain > 0:
                kw_ascii = bool(re.fullmatch(r"[0-9A-Za-z_\\-\\.]+", kw))
                if kw_ascii:
                    high = f"{kw}\uffff"
                    cur.execute(
                        "SELECT id, username, COALESCE(name, username, '') AS name, COALESCE(avatar, '') AS avatar "
                        "FROM users "
                        "WHERE role = 'student' AND id != ? AND username >= ? AND username < ? "
                        "LIMIT ?",
                        (uid, kw, high, remain)
                    )
                    rows.extend(cur.fetchall() or [])
                    remain2 = max(lim - len(rows), 0)
                    if remain2 > 0:
                        cur.execute(
                            "SELECT id, username, COALESCE(name, username, '') AS name, COALESCE(avatar, '') AS avatar "
                            "FROM users "
                            "WHERE role = 'student' AND id != ? AND name IS NOT NULL AND name >= ? AND name < ? "
                            "LIMIT ?",
                            (uid, kw, high, remain2)
                        )
                        rows.extend(cur.fetchall() or [])
                else:
                    cur.execute(
                        "SELECT id, username, COALESCE(name, username, '') AS name, COALESCE(avatar, '') AS avatar "
                        "FROM users "
                        "WHERE role = 'student' AND id != ? AND (username LIKE ? OR (name IS NOT NULL AND name LIKE ?)) "
                        "LIMIT ?",
                        (uid, like_prefix, like_prefix, remain)
                    )
                    rows.extend(cur.fetchall() or [])
        except Exception:
            pass
        conn.close()

        seen = set()
        out = []
        for r in rows:
            rid = str(r["id"] or "")
            if not rid or rid in seen:
                continue
            seen.add(rid)
            out.append({"id": rid, "username": r["username"], "name": r["name"], "avatar": r["avatar"]})
            if len(out) >= lim:
                break
        return out

    out = await asyncio.to_thread(_work)
    try:
        _USER_SEARCH_CACHE[cache_key] = {"ts": now_ts, "users": out}
        if len(_USER_SEARCH_CACHE) > 1000:
            for k, v in list(_USER_SEARCH_CACHE.items())[:200]:
                if (now_ts - float(v.get("ts") or 0)) > _USER_SEARCH_CACHE_TTL_SEC:
                    _USER_SEARCH_CACHE.pop(k, None)
    except Exception:
        pass
    return {"success": True, "users": out}

@app.get("/api/users/me/state")
async def get_me_state(authorization: str = Header(None)):
    user = _require_user(authorization)
    state = _get_user_state(user["id"])
    return {"success": True, "state": state}

@app.put("/api/users/me/state")
async def update_me_state(req: UpdateUserStateRequest, authorization: str = Header(None)):
    user = _require_user(authorization)
    existing = _get_user_state(user["id"])
    daily_checkin = existing.get("daily_checkin") or {}
    if isinstance(req.daily_checkin, dict):
        daily_checkin = {**daily_checkin, **req.daily_checkin}
    practice_done = existing.get("practice_done") or {}
    if isinstance(req.practice_done, dict):
        for k, v in req.practice_done.items():
            if isinstance(v, dict):
                existed_v = practice_done.get(k)
                if isinstance(existed_v, dict):
                    practice_done[k] = {**existed_v, **v}
                else:
                    practice_done[k] = v
            else:
                practice_done[k] = v
    _upsert_user_state(user["id"], daily_checkin, practice_done)
    return {"success": True, "state": {"daily_checkin": daily_checkin, "practice_done": practice_done}}

@app.post("/api/classes/create")
async def create_class(req: CreateClassRequest, authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_teacher(user)
    name = str(req.name or "").strip()
    if len(name) < 1 or len(name) > 30:
        raise HTTPException(status_code=400, detail="班级名称长度需为 1-30 位")
    class_id = f"cls_{secrets.token_hex(8)}"
    code = secrets.token_hex(3).upper()
    conn = _db_connect()
    cur = conn.cursor()
    for _ in range(5):
        try:
            cur.execute("INSERT INTO classes (id, teacher_id, name, code) VALUES (?, ?, ?, ?)", (class_id, user["id"], name, code))
            _ensure_class_group(cur, class_id, name, user["id"])
            conn.commit()
            conn.close()
            return {"success": True, "class": {"id": class_id, "name": name, "code": code}}
        except sqlite3.IntegrityError:
            code = secrets.token_hex(3).upper()
    conn.close()
    raise HTTPException(status_code=500, detail="创建班级失败")

@app.post("/api/classes/join")
async def join_class(req: JoinClassRequest, authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_student(user)
    code = str(req.code or "").strip().upper()
    if len(code) < 4:
        raise HTTPException(status_code=400, detail="班级码不合法")
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, name, code FROM classes WHERE code = ? LIMIT 1", (code,))
    cls = cur.fetchone()
    if not cls:
        conn.close()
        raise HTTPException(status_code=400, detail="班级不存在")
    try:
        cur.execute("INSERT INTO class_members (class_id, student_id) VALUES (?, ?)", (cls["id"], user["id"]))
        _ensure_class_group(cur, cls["id"], cls["name"], "")
        cur.execute(
            "INSERT OR IGNORE INTO conversation_members (conversation_id, user_id, last_read_at, last_read_id) "
            "VALUES (?, ?, CURRENT_TIMESTAMP, (SELECT IFNULL(MAX(id), 0) FROM messages WHERE conversation_id = ?))",
            (_conv_id_class(cls["id"]), user["id"], _conv_id_class(cls["id"]))
        )
        conn.commit()
    except sqlite3.IntegrityError:
        try:
            _ensure_class_group(cur, cls["id"], cls["name"], "")
            cur.execute(
                "INSERT OR IGNORE INTO conversation_members (conversation_id, user_id, last_read_at, last_read_id) "
                "VALUES (?, ?, CURRENT_TIMESTAMP, (SELECT IFNULL(MAX(id), 0) FROM messages WHERE conversation_id = ?))",
                (_conv_id_class(cls["id"]), user["id"], _conv_id_class(cls["id"]))
            )
            conn.commit()
        except Exception:
            pass
    conn.close()
    return {"success": True, "class": {"id": cls["id"], "name": cls["name"], "code": cls["code"]}}

@app.get("/api/classes/mine")
async def my_classes(authorization: str = Header(None)):
    user = _require_user(authorization)
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if user.get("role") == "teacher":
        cur.execute("SELECT id, name, code FROM classes WHERE teacher_id = ? ORDER BY created_at DESC", (user["id"],))
        rows = cur.fetchall() or []
        conn.close()
        return {"success": True, "role": "teacher", "classes": [{"id": r["id"], "name": r["name"], "code": r["code"]} for r in rows]}
    cur.execute(
        "SELECT c.id, c.name, c.code FROM class_members m JOIN classes c ON c.id = m.class_id "
        "WHERE m.student_id = ? ORDER BY c.created_at DESC",
        (user["id"],)
    )
    rows = cur.fetchall() or []
    conn.close()
    return {"success": True, "role": "student", "classes": [{"id": r["id"], "name": r["name"], "code": r["code"]} for r in rows]}

@app.get("/api/classes/{class_id}/members")
async def class_members(class_id: str, authorization: str = Header(None), limit: int = 300):
    user = _require_user(authorization)
    cid = str(class_id or "").strip()
    if not cid:
        raise HTTPException(status_code=400, detail="缺少班级")
    lim = int(limit or 300)
    if lim <= 0:
        lim = 300
    if lim > 500:
        lim = 500

    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, name, code, teacher_id FROM classes WHERE id = ? LIMIT 1", (cid,))
    cls = cur.fetchone()
    if not cls:
        conn.close()
        raise HTTPException(status_code=404, detail="班级不存在")

    role = str(user.get("role") or "")
    if role == "teacher":
        if str(cls["teacher_id"] or "") != str(user["id"]):
            conn.close()
            raise HTTPException(status_code=403, detail="无权限操作该班级")
    else:
        cur.execute("SELECT 1 FROM class_members WHERE class_id = ? AND student_id = ? LIMIT 1", (cid, str(user["id"])))
        if not cur.fetchone():
            conn.close()
            raise HTTPException(status_code=403, detail="无权限查看该班级")

    teacher = None
    tid = str(cls["teacher_id"] or "").strip()
    if tid:
        cur.execute(
            "SELECT id, username, COALESCE(name, username, '') AS name, COALESCE(avatar, '') AS avatar "
            "FROM users WHERE id = ? LIMIT 1",
            (tid,)
        )
        tr = cur.fetchone()
        if tr:
            teacher = {"id": str(tr["id"]), "username": str(tr["username"]), "name": str(tr["name"]), "avatar": str(tr["avatar"] or "")}

    cur.execute(
        "SELECT u.id, u.username, COALESCE(u.name, u.username, '') AS name, COALESCE(u.avatar, '') AS avatar "
        "FROM class_members m JOIN users u ON u.id = m.student_id "
        "WHERE m.class_id = ? ORDER BY u.username ASC LIMIT ?",
        (cid, lim)
    )
    rows = cur.fetchall() or []
    conn.close()
    students = [{"id": str(r["id"]), "username": str(r["username"]), "name": str(r["name"]), "avatar": str(r["avatar"] or "")} for r in rows]
    return {
        "success": True,
        "class": {"id": str(cls["id"]), "name": str(cls["name"]), "code": str(cls["code"] or "")},
        "teacher": teacher,
        "students": students
    }

@app.post("/api/classes/leave")
async def leave_class(req: LeaveClassRequest, authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_student(user)
    class_id = str(req.class_id or "").strip()
    if not class_id:
        raise HTTPException(status_code=400, detail="缺少班级")
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM class_members WHERE class_id = ? AND student_id = ?", (class_id, user["id"]))
    cur.execute("DELETE FROM conversation_members WHERE conversation_id = ? AND user_id = ?", (_conv_id_class(class_id), user["id"]))
    conn.commit()
    conn.close()
    return {"success": True}

@app.post("/api/classes/dissolve")
async def dissolve_class(req: DissolveClassRequest, authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_teacher(user)
    class_id = str(req.class_id or "").strip()
    if not class_id:
        raise HTTPException(status_code=400, detail="缺少班级")
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute("SELECT id FROM classes WHERE id = ? AND teacher_id = ? LIMIT 1", (class_id, user["id"]))
    owned = cur.fetchone()
    if not owned:
        conn.close()
        raise HTTPException(status_code=403, detail="无权限操作该班级")
    cur.execute("DELETE FROM checkin_tasks WHERE class_id = ?", (class_id,))
    cur.execute("DELETE FROM class_members WHERE class_id = ?", (class_id,))
    conv_id = _conv_id_class(class_id)
    cur.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
    cur.execute("DELETE FROM conversation_members WHERE conversation_id = ?", (conv_id,))
    cur.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    cur.execute("DELETE FROM classes WHERE id = ?", (class_id,))
    conn.commit()
    conn.close()
    return {"success": True}

class FriendRequestCreate(BaseModel):
    to_user_id: str

class FriendRequestRespond(BaseModel):
    request_id: int
    action: str

class MessageSendRequest(BaseModel):
    conversation_id: str
    content: str

class MessageSendDmRequest(BaseModel):
    to_user_id: str
    content: str

class MessageReadRequest(BaseModel):
    conversation_id: str

def _are_friends(cur, a: str, b: str) -> bool:
    cur.execute("SELECT 1 FROM friends WHERE user_id = ? AND friend_id = ? LIMIT 1", (a, b))
    return cur.fetchone() is not None

def _share_class(cur, a: str, b: str) -> bool:
    cur.execute(
        "SELECT 1 FROM class_members m1 JOIN class_members m2 ON m1.class_id = m2.class_id "
        "WHERE m1.student_id = ? AND m2.student_id = ? LIMIT 1",
        (a, b)
    )
    return cur.fetchone() is not None

def _can_dm(cur, sender: dict, to_user_id: str) -> bool:
    sid = str(sender.get("id") or "")
    tid = str(to_user_id or "")
    if not sid or not tid or sid == tid:
        return False
    if _are_friends(cur, sid, tid):
        return True
    if str(sender.get("role") or "") == "teacher":
        cur.execute(
            "SELECT 1 FROM classes c JOIN class_members m ON m.class_id = c.id "
            "WHERE c.teacher_id = ? AND m.student_id = ? LIMIT 1",
            (sid, tid)
        )
        return cur.fetchone() is not None
    cur.execute("SELECT 1 FROM users WHERE id = ? AND role = 'teacher' LIMIT 1", (tid,))
    if cur.fetchone() is not None:
        cur.execute(
            "SELECT 1 FROM classes c JOIN class_members m ON m.class_id = c.id "
            "WHERE c.teacher_id = ? AND m.student_id = ? LIMIT 1",
            (tid, sid)
        )
        return cur.fetchone() is not None
    return _share_class(cur, sid, tid)

@app.post("/api/friends/request")
async def create_friend_request(req: FriendRequestCreate, authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_student(user)
    to_id = str(req.to_user_id or "").strip()
    if not to_id or to_id == str(user["id"]):
        raise HTTPException(status_code=400, detail="用户不合法")
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, role FROM users WHERE id = ? LIMIT 1", (to_id,))
    row = cur.fetchone()
    if not row or str(row["role"] or "") != "student":
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")
    if _are_friends(cur, user["id"], to_id):
        conn.close()
        return {"success": True, "message": "已是好友"}
    cur.execute(
        "SELECT id FROM friend_requests WHERE from_user_id = ? AND to_user_id = ? AND status = 'pending' LIMIT 1",
        (user["id"], to_id)
    )
    if cur.fetchone():
        conn.close()
        return {"success": True, "message": "已发送申请"}
    cur.execute(
        "INSERT INTO friend_requests (from_user_id, to_user_id, status) VALUES (?, ?, 'pending')",
        (user["id"], to_id)
    )
    conn.commit()
    conn.close()
    return {"success": True}

@app.post("/api/friends/respond")
async def respond_friend_request(req: FriendRequestRespond, authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_student(user)
    rid = int(req.request_id or 0)
    action = str(req.action or "").strip().lower()
    if rid <= 0 or action not in ("accept", "reject"):
        raise HTTPException(status_code=400, detail="参数不合法")
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM friend_requests WHERE id = ? LIMIT 1", (rid,))
    fr = cur.fetchone()
    if not fr or str(fr["to_user_id"] or "") != str(user["id"]):
        conn.close()
        raise HTTPException(status_code=404, detail="申请不存在")
    if str(fr["status"] or "") != "pending":
        conn.close()
        return {"success": True}
    if action == "reject":
        cur.execute("UPDATE friend_requests SET status = 'rejected' WHERE id = ?", (rid,))
        conn.commit()
        conn.close()
        return {"success": True}

    from_id = str(fr["from_user_id"] or "")
    cur.execute("UPDATE friend_requests SET status = 'accepted' WHERE id = ?", (rid,))
    cur.execute("INSERT OR IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)", (user["id"], from_id))
    cur.execute("INSERT OR IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)", (from_id, user["id"]))
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/api/friends/list")
async def list_friends(authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_student(user)
    uid = str(user["id"])

    lock = _get_async_lock("friends:list", uid)
    async with lock:
        def _work():
            conn = _db_connect()
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT u.id, COALESCE(u.name, u.username, '') AS name, COALESCE(u.avatar, '') AS avatar "
                "FROM friends f JOIN users u ON u.id = f.friend_id "
                "WHERE f.user_id = ? ORDER BY u.created_at ASC",
                (uid,)
            )
            rows = cur.fetchall() or []
            conn.close()
            return [{"id": r["id"], "name": r["name"], "avatar": r["avatar"]} for r in rows]

        friends_out = await asyncio.to_thread(_work)
        return {"success": True, "friends": friends_out}

@app.get("/api/friends/requests")
async def list_friend_requests(authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_student(user)
    uid = str(user["id"])

    lock = _get_async_lock("friends:requests", uid)
    async with lock:
        def _work():
            conn = _db_connect()
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT fr.id, fr.from_user_id, COALESCE(u.name, u.username, '') AS from_name, COALESCE(u.avatar, '') AS from_avatar, "
                "fr.status, fr.created_at "
                "FROM friend_requests fr JOIN users u ON u.id = fr.from_user_id "
                "WHERE fr.to_user_id = ? ORDER BY fr.created_at DESC LIMIT 50",
                (uid,)
            )
            incoming = [
                {
                    "id": int(r["id"]),
                    "fromUserId": r["from_user_id"],
                    "fromName": r["from_name"],
                    "fromAvatar": r["from_avatar"],
                    "status": r["status"],
                    "createdAt": str(r["created_at"] or "")
                }
                for r in (cur.fetchall() or [])
            ]
            cur.execute(
                "SELECT fr.id, fr.to_user_id, COALESCE(u.name, u.username, '') AS to_name, COALESCE(u.avatar, '') AS to_avatar, "
                "fr.status, fr.created_at "
                "FROM friend_requests fr JOIN users u ON u.id = fr.to_user_id "
                "WHERE fr.from_user_id = ? ORDER BY fr.created_at DESC LIMIT 50",
                (uid,)
            )
            outgoing = [
                {
                    "id": int(r["id"]),
                    "toUserId": r["to_user_id"],
                    "toName": r["to_name"],
                    "toAvatar": r["to_avatar"],
                    "status": r["status"],
                    "createdAt": str(r["created_at"] or "")
                }
                for r in (cur.fetchall() or [])
            ]
            conn.close()
            return incoming, outgoing

        incoming, outgoing = await asyncio.to_thread(_work)
        return {"success": True, "incoming": incoming, "outgoing": outgoing}

@app.get("/api/messages/unread-count")
async def messages_unread_count(authorization: str = Header(None)):
    user = _require_user(authorization)
    uid = str(user["id"])
    now_ts = time.time()
    cached = _UNREAD_COUNT_CACHE.get(uid)
    if cached and (now_ts - float(cached.get("ts") or 0)) < _MESSAGES_CACHE_TTL_SEC:
        return {"success": True, "unread": int(cached.get("unread") or 0)}

    lock = _get_async_lock("messages:unread", uid)
    async with lock:
        cached2 = _UNREAD_COUNT_CACHE.get(uid)
        if cached2 and (now_ts - float(cached2.get("ts") or 0)) < _MESSAGES_CACHE_TTL_SEC:
            return {"success": True, "unread": int(cached2.get("unread") or 0)}

        def _work():
            conn = _db_connect()
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                WITH my AS (
                  SELECT conversation_id, COALESCE(last_read_id, 0) AS last_read_id
                  FROM conversation_members
                  WHERE user_id = ?
                )
                SELECT COUNT(*) AS unread
                FROM messages m
                JOIN my ON my.conversation_id = m.conversation_id
                WHERE m.sender_id != ?
                  AND m.id > my.last_read_id
                """,
                (uid, uid)
            )
            row = cur.fetchone()
            conn.close()
            return int(row["unread"] or 0) if row else 0

        n = await asyncio.to_thread(_work)
    try:
        _UNREAD_COUNT_CACHE[uid] = {"ts": now_ts, "unread": n}
        if len(_UNREAD_COUNT_CACHE) > 5000:
            for k, v in list(_UNREAD_COUNT_CACHE.items())[:1000]:
                if (now_ts - float(v.get("ts") or 0)) > _MESSAGES_CACHE_TTL_SEC:
                    _UNREAD_COUNT_CACHE.pop(k, None)
    except Exception:
        pass
    return {"success": True, "unread": n}

@app.get("/api/messages/conversations")
async def list_conversations(authorization: str = Header(None), x_trace_id: str = Header(None)):
    user = _require_user(authorization)
    uid = str(user["id"])
    now_ts = time.time()
    cached = _CONVERSATIONS_CACHE.get(uid)
    if cached and (now_ts - float(cached.get("ts") or 0)) < _MESSAGES_CACHE_TTL_SEC:
        return {"success": True, "conversations": cached.get("conversations") or []}

    role = str(user.get("role") or "")
    trace_id = x_trace_id or f"conv-{int(time.time() * 1000)}"

    lock = _get_async_lock("messages:conversations", uid)
    async with lock:
        cached2 = _CONVERSATIONS_CACHE.get(uid)
        if cached2 and (now_ts - float(cached2.get("ts") or 0)) < _MESSAGES_CACHE_TTL_SEC:
            return {"success": True, "conversations": cached2.get("conversations") or []}

    def _work():
        t0 = time.perf_counter()
        conn = _db_connect()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            if role == "teacher":
                cur.execute("SELECT id, name FROM classes WHERE teacher_id = ?", (uid,))
                for c in (cur.fetchall() or []):
                    _ensure_class_group(cur, c["id"], c["name"], uid)
                conn.commit()
            else:
                cur.execute(
                    "SELECT c.id, c.name, c.teacher_id FROM class_members m JOIN classes c ON c.id = m.class_id WHERE m.student_id = ?",
                    (uid,)
                )
                for c in (cur.fetchall() or []):
                    _ensure_class_group(cur, c["id"], c["name"], str(c["teacher_id"] or ""))
                    cur.execute(
                        "INSERT OR IGNORE INTO conversation_members (conversation_id, user_id, last_read_at, last_read_id) "
                        "VALUES (?, ?, CURRENT_TIMESTAMP, (SELECT IFNULL(MAX(id), 0) FROM messages WHERE conversation_id = ?))",
                        (_conv_id_class(c["id"]), uid, _conv_id_class(c["id"]))
                    )
                conn.commit()
        except Exception:
            pass
        cur.execute(
            """
            WITH my AS (
              SELECT conversation_id, last_read_at, COALESCE(last_read_id, 0) AS last_read_id
              FROM conversation_members
              WHERE user_id = ?
            ),
            last_id AS (
              SELECT
                my.conversation_id,
                (
                  SELECT id
                  FROM messages
                  WHERE conversation_id = my.conversation_id
                  ORDER BY id DESC
                  LIMIT 1
                ) AS last_message_id
              FROM my
            ),
            unread AS (
              SELECT m.conversation_id, COUNT(*) AS unread_count
              FROM messages m
              JOIN my ON my.conversation_id = m.conversation_id
              WHERE m.sender_id != ?
                AND m.id > my.last_read_id
              GROUP BY m.conversation_id
            )
            SELECT
              c.id AS conversation_id,
              c.type AS type,
              c.title AS title,
              c.class_id AS class_id,
              my.last_read_at AS last_read_at,
              my.last_read_id AS last_read_id,
              COALESCE(unread.unread_count, 0) AS unread_count,
              lm.id AS last_message_id,
              lm.content AS last_message_content,
              lm.created_at AS last_message_at,
              lm.sender_id AS last_message_sender,
              u2.id AS peer_id,
              COALESCE(u2.name, u2.username, '') AS peer_name,
              COALESCE(u2.avatar, '') AS peer_avatar
            FROM my
            JOIN conversations c ON c.id = my.conversation_id
            LEFT JOIN last_id lid ON lid.conversation_id = c.id
            LEFT JOIN messages lm ON lm.id = lid.last_message_id
            LEFT JOIN unread ON unread.conversation_id = c.id
            LEFT JOIN conversation_members cm2 ON cm2.conversation_id = c.id AND c.type = 'dm' AND cm2.user_id != ?
            LEFT JOIN users u2 ON u2.id = cm2.user_id
            ORDER BY COALESCE(lm.id, 0) DESC, c.created_at DESC
            LIMIT 200
            """,
            (uid, uid, uid)
        )
        rows = cur.fetchall() or []
        conn.close()
        out = []
        for r in rows:
            item = {
                "id": r["conversation_id"],
                "type": r["type"],
                "title": r["title"] or "",
                "classId": r["class_id"] or "",
                "unread": int(r["unread_count"] or 0),
                "lastMessage": {
                    "id": int(r["last_message_id"] or 0) if r["last_message_id"] is not None else 0,
                    "content": r["last_message_content"] or "",
                    "at": str(r["last_message_at"] or ""),
                    "senderId": r["last_message_sender"] or ""
                }
            }
            if str(r["type"] or "") == "dm":
                item["peer"] = {
                    "id": r["peer_id"] or "",
                    "name": r["peer_name"] or "",
                    "avatar": r["peer_avatar"] or ""
                }
            out.append(item)
        return out

    out = await asyncio.to_thread(_work)
    try:
        _CONVERSATIONS_CACHE[uid] = {"ts": now_ts, "conversations": out}
        if len(_CONVERSATIONS_CACHE) > 5000:
            for k, v in list(_CONVERSATIONS_CACHE.items())[:1000]:
                if (now_ts - float(v.get("ts") or 0)) > _MESSAGES_CACHE_TTL_SEC:
                    _CONVERSATIONS_CACHE.pop(k, None)
    except Exception:
        pass
    return {"success": True, "conversations": out}

@app.get("/api/messages/{conversation_id}")
async def get_messages(
    conversation_id: str,
    limit: int = Query(50),
    before_id: int = Query(0),
    after_id: int = Query(0),
    authorization: str = Header(None)
):
    user = _require_user(authorization)
    uid = str(user["id"])
    cid = str(conversation_id or "").strip()
    lim = int(limit or 50)
    if lim <= 0:
        lim = 50
    if lim > 200:
        lim = 200

    def _work():
        conn = _db_connect()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM conversation_members WHERE conversation_id = ? AND user_id = ? LIMIT 1",
            (cid, uid)
        )
        if not cur.fetchone():
            conn.close()
            return False, []
        if after_id and after_id > 0:
            cur.execute(
                "SELECT m.id, m.conversation_id, m.sender_id, m.content, m.created_at, "
                "COALESCE(u.avatar, '') AS sender_avatar, COALESCE(u.name, u.username, '') AS sender_name "
                "FROM messages m LEFT JOIN users u ON u.id = m.sender_id "
                "WHERE m.conversation_id = ? AND m.id > ? ORDER BY m.id ASC LIMIT ?",
                (cid, int(after_id), lim)
            )
        elif before_id and before_id > 0:
            cur.execute(
                "SELECT m.id, m.conversation_id, m.sender_id, m.content, m.created_at, "
                "COALESCE(u.avatar, '') AS sender_avatar, COALESCE(u.name, u.username, '') AS sender_name "
                "FROM messages m LEFT JOIN users u ON u.id = m.sender_id "
                "WHERE m.conversation_id = ? AND m.id < ? ORDER BY m.id DESC LIMIT ?",
                (cid, int(before_id), lim)
            )
        else:
            cur.execute(
                "SELECT m.id, m.conversation_id, m.sender_id, m.content, m.created_at, "
                "COALESCE(u.avatar, '') AS sender_avatar, COALESCE(u.name, u.username, '') AS sender_name "
                "FROM messages m LEFT JOIN users u ON u.id = m.sender_id "
                "WHERE m.conversation_id = ? ORDER BY m.id DESC LIMIT ?",
                (cid, lim)
            )
        rows = cur.fetchall() or []
        conn.close()
        if not (after_id and after_id > 0):
            rows = list(reversed(rows))
        out = [
            {
                "id": int(r["id"]),
                "conversationId": r["conversation_id"],
                "senderId": r["sender_id"],
                "senderAvatar": r["sender_avatar"],
                "senderName": r["sender_name"],
                "content": r["content"],
                "createdAt": str(r["created_at"] or "")
            }
            for r in rows
        ]
        return True, out

    ok, out = await asyncio.to_thread(_work)
    if not ok:
        raise HTTPException(status_code=403, detail="无权限访问该会话")
    return {"success": True, "messages": out}

@app.post("/api/messages/read")
async def mark_read(req: MessageReadRequest, authorization: str = Header(None)):
    user = _require_user(authorization)
    uid = str(user["id"])
    cid = str(req.conversation_id or "").strip()
    if not cid:
        raise HTTPException(status_code=400, detail="缺少会话")
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE conversation_members "
        "SET last_read_at = CURRENT_TIMESTAMP, "
        "    last_read_id = (SELECT IFNULL(MAX(id), 0) FROM messages WHERE conversation_id = ?) "
        "WHERE conversation_id = ? AND user_id = ?",
        (cid, cid, uid)
    )
    conn.commit()
    conn.close()
    try:
        _UNREAD_COUNT_CACHE.pop(uid, None)
        _CONVERSATIONS_CACHE.pop(uid, None)
    except Exception:
        pass
    return {"success": True}

@app.post("/api/messages/send")
async def send_message(req: MessageSendRequest, authorization: str = Header(None)):
    user = _require_user(authorization)
    uid = str(user["id"])
    cid = str(req.conversation_id or "").strip()
    content = str(req.content or "").strip()
    if not cid or not content:
        raise HTTPException(status_code=400, detail="参数不合法")
    if len(content) > 2000:
        raise HTTPException(status_code=400, detail="消息过长")
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM conversation_members WHERE conversation_id = ? AND user_id = ? LIMIT 1",
        (cid, uid)
    )
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="无权限发送")
    cur.execute(
        "INSERT INTO messages (conversation_id, sender_id, content) VALUES (?, ?, ?)",
        (cid, uid, content)
    )
    last_id = int(cur.lastrowid or 0)
    cur.execute(
        "UPDATE conversation_members SET last_read_at = CURRENT_TIMESTAMP, last_read_id = ? WHERE conversation_id = ? AND user_id = ?",
        (last_id, cid, uid)
    )
    conn.commit()
    conn.close()
    try:
        _UNREAD_COUNT_CACHE.pop(uid, None)
        _CONVERSATIONS_CACHE.pop(uid, None)
    except Exception:
        pass
    return {"success": True}

@app.post("/api/messages/send-dm")
async def send_dm(req: MessageSendDmRequest, authorization: str = Header(None)):
    user = _require_user(authorization)
    uid = str(user["id"])
    to_id = str(req.to_user_id or "").strip()
    content = str(req.content or "").strip()
    if not to_id or not content:
        raise HTTPException(status_code=400, detail="参数不合法")
    if len(content) > 2000:
        raise HTTPException(status_code=400, detail="消息过长")
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id = ? LIMIT 1", (to_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")
    if not _can_dm(cur, user, to_id):
        conn.close()
        raise HTTPException(status_code=403, detail="无法私信该用户")
    cid = _conv_id_dm(uid, to_id)
    cur.execute("INSERT OR IGNORE INTO conversations (id, type, title) VALUES (?, 'dm', '')", (cid,))
    cur.execute(
        "INSERT OR IGNORE INTO conversation_members (conversation_id, user_id, last_read_at, last_read_id) "
        "VALUES (?, ?, CURRENT_TIMESTAMP, (SELECT IFNULL(MAX(id), 0) FROM messages WHERE conversation_id = ?))",
        (cid, uid, cid)
    )
    cur.execute(
        "INSERT OR IGNORE INTO conversation_members (conversation_id, user_id, last_read_at, last_read_id) VALUES (?, ?, NULL, 0)",
        (cid, to_id)
    )
    cur.execute(
        "INSERT INTO messages (conversation_id, sender_id, content) VALUES (?, ?, ?)",
        (cid, uid, content)
    )
    last_id = int(cur.lastrowid or 0)
    cur.execute(
        "UPDATE conversation_members SET last_read_at = CURRENT_TIMESTAMP, last_read_id = ? WHERE conversation_id = ? AND user_id = ?",
        (last_id, cid, uid)
    )
    conn.commit()
    conn.close()
    try:
        _UNREAD_COUNT_CACHE.pop(uid, None)
        _CONVERSATIONS_CACHE.pop(uid, None)
        _UNREAD_COUNT_CACHE.pop(to_id, None)
        _CONVERSATIONS_CACHE.pop(to_id, None)
    except Exception:
        pass
    return {"success": True, "conversation_id": cid}

@app.post("/api/messages/open-dm")
async def open_dm(req: MessageSendDmRequest, authorization: str = Header(None)):
    user = _require_user(authorization)
    uid = str(user["id"])
    to_id = str(req.to_user_id or "").strip()
    if not to_id:
        raise HTTPException(status_code=400, detail="参数不合法")
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id = ? LIMIT 1", (to_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")
    if not _can_dm(cur, user, to_id):
        conn.close()
        raise HTTPException(status_code=403, detail="无法私信该用户")
    cid = _conv_id_dm(uid, to_id)
    cur.execute("INSERT OR IGNORE INTO conversations (id, type, title) VALUES (?, 'dm', '')", (cid,))
    cur.execute(
        "INSERT OR IGNORE INTO conversation_members (conversation_id, user_id, last_read_at, last_read_id) "
        "VALUES (?, ?, CURRENT_TIMESTAMP, (SELECT IFNULL(MAX(id), 0) FROM messages WHERE conversation_id = ?))",
        (cid, uid, cid)
    )
    cur.execute(
        "INSERT OR IGNORE INTO conversation_members (conversation_id, user_id, last_read_at, last_read_id) VALUES (?, ?, NULL, 0)",
        (cid, to_id)
    )
    conn.commit()
    conn.close()
    try:
        _UNREAD_COUNT_CACHE.pop(uid, None)
        _CONVERSATIONS_CACHE.pop(uid, None)
        _UNREAD_COUNT_CACHE.pop(to_id, None)
        _CONVERSATIONS_CACHE.pop(to_id, None)
    except Exception:
        pass
    return {"success": True, "conversation_id": cid}

@app.post("/api/teacher/tasks")
async def create_task(req: CreateTaskRequest, authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_teacher(user)
    class_id = str(req.class_id or "").strip()
    title = str(req.title or "").strip()
    language = str(req.language or "").strip()
    if not class_id:
        raise HTTPException(status_code=400, detail="缺少班级")
    if len(title) < 1 or len(title) > 60:
        raise HTTPException(status_code=400, detail="题目标题长度需为 1-60 位")
    if language not in ("javascript", "python", "java", "c"):
        raise HTTPException(status_code=400, detail="语言不支持")
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id FROM classes WHERE id = ? AND teacher_id = ? LIMIT 1", (class_id, user["id"]))
    owned = cur.fetchone()
    if not owned:
        conn.close()
        raise HTTPException(status_code=403, detail="无权限操作该班级")
    task_id = f"tsk_{secrets.token_hex(10)}"
    cur.execute(
        "INSERT INTO checkin_tasks (id, teacher_id, class_id, title, description, language, starter_code, expected_output, solution_code, due_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (task_id, user["id"], class_id, title, str(req.description or ""), language, str(req.starter_code or ""), str(req.expected_output or ""), str(req.solution_code or ""), str(req.due_at or ""))
    )
    conn.commit()
    conn.close()
    return {"success": True, "task": {"id": task_id}}

@app.get("/api/teacher/tasks")
async def list_teacher_tasks(class_id: str = "", authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_teacher(user)
    class_id = str(class_id or "").strip()
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if class_id:
        cur.execute("SELECT id FROM classes WHERE id = ? AND teacher_id = ? LIMIT 1", (class_id, user["id"]))
        owned = cur.fetchone()
        if not owned:
            conn.close()
            raise HTTPException(status_code=403, detail="无权限操作该班级")
        cur.execute(
            "SELECT t.id, t.class_id, c.name AS class_name, c.code AS class_code, "
            "t.title, t.description, t.language, t.starter_code, t.expected_output, t.solution_code, t.due_at, t.created_at "
            "FROM checkin_tasks t JOIN classes c ON c.id = t.class_id "
            "WHERE t.teacher_id = ? AND t.class_id = ? "
            "ORDER BY t.created_at DESC",
            (user["id"], class_id)
        )
    else:
        cur.execute(
            "SELECT t.id, t.class_id, c.name AS class_name, c.code AS class_code, "
            "t.title, t.description, t.language, t.starter_code, t.expected_output, t.solution_code, t.due_at, t.created_at "
            "FROM checkin_tasks t JOIN classes c ON c.id = t.class_id "
            "WHERE t.teacher_id = ? "
            "ORDER BY t.created_at DESC",
            (user["id"],)
        )
    rows = cur.fetchall() or []
    conn.close()
    tasks = []
    for r in rows:
        tasks.append({
            "id": r["id"],
            "class_id": r["class_id"],
            "class_name": r["class_name"],
            "class_code": r["class_code"],
            "title": r["title"],
            "description": r["description"] or "",
            "language": r["language"],
            "starterCode": r["starter_code"] or "",
            "expectedOutput": r["expected_output"] or "",
            "solutionCode": r["solution_code"] or "",
            "dueAt": r["due_at"] or "",
            "createdAt": str(r["created_at"] or "")
        })
    return {"success": True, "tasks": tasks}

@app.get("/api/teacher/classes/summary")
async def teacher_classes_summary(authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_teacher(user)
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT c.id, c.name, c.code, c.created_at, "
        "COALESCE(COUNT(m.student_id), 0) AS student_count "
        "FROM classes c LEFT JOIN class_members m ON m.class_id = c.id "
        "WHERE c.teacher_id = ? "
        "GROUP BY c.id ORDER BY c.created_at DESC",
        (user["id"],)
    )
    rows = cur.fetchall() or []
    conn.close()
    classes = []
    for r in rows:
        classes.append({
            "id": r["id"],
            "name": r["name"],
            "code": r["code"],
            "createdAt": str(r["created_at"] or ""),
            "studentCount": int(r["student_count"] or 0)
        })
    return {"success": True, "classes": classes}

@app.get("/api/teacher/classes/students")
async def teacher_class_students(class_id: str = "", authorization: str = Header(None), limit: int = 120):
    user = _require_user(authorization)
    _require_teacher(user)
    class_id = str(class_id or "").strip()
    if not class_id:
        raise HTTPException(status_code=400, detail="缺少班级")
    lim = int(limit or 120)
    if lim <= 0:
        lim = 120
    if lim > 300:
        lim = 300

    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, name, code FROM classes WHERE id = ? AND teacher_id = ? LIMIT 1", (class_id, user["id"]))
    cls = cur.fetchone()
    if not cls:
        conn.close()
        raise HTTPException(status_code=403, detail="无权限操作该班级")

    cur.execute(
        "SELECT u.id, u.username, u.role, u.name, u.avatar "
        "FROM class_members m JOIN users u ON u.id = m.student_id "
        "WHERE m.class_id = ? ORDER BY u.username ASC LIMIT ?",
        (class_id, lim)
    )
    students = cur.fetchall() or []
    conn.close()

    student_ids = [str(r["id"]) for r in students]
    stats_map = {}
    if student_ids:
        conn2 = _db_connect()
        cur2 = conn2.cursor()
        placeholders = ",".join(["?"] * len(student_ids))
        cur2.execute(
            f"SELECT student_id, COUNT(*) AS total, "
            f"SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS success_count, "
            f"COUNT(DISTINCT problem_id) AS problems_attempted "
            f"FROM code_submissions WHERE student_id IN ({placeholders}) "
            f"GROUP BY student_id",
            tuple(student_ids)
        )
        for row in cur2.fetchall() or []:
            sid = str(row[0] or "")
            total = int(row[1] or 0)
            succ = int(row[2] or 0)
            attempted = int(row[3] or 0)
            stats_map[sid] = {
                "total_submissions": total,
                "success_count": succ,
                "success_rate": round(succ / total * 100, 2) if total > 0 else 0,
                "problems_attempted": attempted
            }
        conn2.close()

    weak_map = {sid: {} for sid in student_ids}
    if student_ids:
        try:
            conn3 = _db_connect()
            conn3.row_factory = sqlite3.Row
            cur3 = conn3.cursor()
            placeholders = ",".join(["?"] * len(student_ids))
            max_fail_rows = min(5000, max(800, len(student_ids) * 80))
            cur3.execute(
                f"SELECT student_id, code, error FROM code_submissions "
                f"WHERE student_id IN ({placeholders}) AND success = 0 "
                f"ORDER BY created_at DESC LIMIT ?",
                tuple(student_ids) + (max_fail_rows,)
            )
            rows = cur3.fetchall() or []
            conn3.close()
            per_student_seen = {sid: 0 for sid in student_ids}
            per_student_cap = 200
            for r in rows:
                sid = str(r["student_id"] or "")
                if sid not in weak_map:
                    continue
                if per_student_seen.get(sid, 0) >= per_student_cap:
                    continue
                per_student_seen[sid] = per_student_seen.get(sid, 0) + 1
                topic = _classify_knowledge_point(str(r["error"] or ""), str(r["code"] or ""))
                weak_map[sid][topic] = weak_map[sid].get(topic, 0) + 1
        except Exception:
            weak_map = {sid: {} for sid in student_ids}

    out = []
    for r in students:
        sid = str(r["id"])
        st = stats_map.get(sid) or {"total_submissions": 0, "success_count": 0, "success_rate": 0, "problems_attempted": 0}
        buckets = weak_map.get(sid) or {}
        topics = sorted(buckets.items(), key=lambda x: x[1], reverse=True)[:12]
        out.append({
            "id": sid,
            "username": r["username"],
            "name": r["name"] or r["username"],
            "avatar": r["avatar"] or "",
            "stats": st,
            "weakTopics": [{"topic": t, "count": c} for t, c in topics]
        })
    return {"success": True, "class": {"id": cls["id"], "name": cls["name"], "code": cls["code"]}, "students": out}

@app.get("/api/student/tasks")
async def list_student_tasks(authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_student(user)
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT t.id, t.class_id, t.title, t.description, t.language, t.starter_code, t.expected_output, t.solution_code, t.due_at, t.created_at, c.name AS class_name "
        "FROM class_members m JOIN checkin_tasks t ON t.class_id = m.class_id "
        "JOIN classes c ON c.id = m.class_id WHERE m.student_id = ? "
        "ORDER BY CASE WHEN t.due_at IS NULL OR t.due_at = '' THEN 1 ELSE 0 END, t.due_at ASC, t.created_at DESC",
        (user["id"],)
    )
    rows = cur.fetchall() or []
    task_ids = [str(r["id"] or "") for r in rows]
    unlocked = set()
    if task_ids:
        placeholders = ",".join(["?"] * len(task_ids))
        cur.execute(
            f"SELECT key FROM solution_unlocks WHERE user_id = ? AND kind = 'task' AND key IN ({placeholders})",
            (str(user["id"]), *task_ids)
        )
        unlocked = {str(x[0] or "") for x in (cur.fetchall() or [])}
    conn.close()
    tasks = []
    for r in rows:
        tid = str(r["id"] or "")
        is_unlocked = tid in unlocked
        tasks.append({
            "id": tid,
            "class_id": r["class_id"],
            "class_name": r["class_name"],
            "title": r["title"],
            "description": r["description"] or "",
            "language": r["language"],
            "starterCode": r["starter_code"] or "",
            "expectedOutput": r["expected_output"] or "",
            "solutionCode": (r["solution_code"] or "") if is_unlocked else "",
            "solutionUnlocked": is_unlocked,
            "dueAt": r["due_at"] or ""
        })
    return {"success": True, "tasks": tasks}

class UnlockDailyPracticeSolutionRequest(BaseModel):
    exercise_id: str

@app.post("/api/daily-practice/solution/unlock")
async def unlock_daily_practice_solution(req: UnlockDailyPracticeSolutionRequest, authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_student(user)
    ex_id = str(req.exercise_id or "").strip()
    if not ex_id:
        raise HTTPException(status_code=400, detail="缺少exercise_id")

    uid = str(user["id"])
    cost = 20
    conn = _db_connect()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            "SELECT 1 FROM solution_unlocks WHERE user_id = ? AND kind = 'daily' AND key = ? LIMIT 1",
            (uid, ex_id)
        )
        if cur.fetchone():
            cur.execute("SELECT COALESCE(SUM(change), 0) FROM points_logs WHERE user_id = ?", (uid,))
            total = int(cur.fetchone()[0] or 0)
            conn.commit()
            conn.close()
            return {"success": True, "unlocked": True, "points": max(total, 0)}

        cur.execute("SELECT COALESCE(SUM(change), 0) FROM points_logs WHERE user_id = ?", (uid,))
        total = int(cur.fetchone()[0] or 0)
        if total < 0:
            total = 0
        if total < cost:
            conn.rollback()
            conn.close()
            return {"success": False, "message": "积分不足"}

        cur.execute(
            "INSERT OR IGNORE INTO solution_unlocks (user_id, kind, key) VALUES (?, 'daily', ?)",
            (uid, ex_id)
        )
        _add_points(cur, uid, -cost, "solution", f"解锁参考答案：{ex_id}")
        conn.commit()
        conn.close()
        return {"success": True, "unlocked": True, "points": total - cost}
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        return {"success": False, "message": "解锁失败"}

@app.post("/api/student/tasks/{task_id}/solution/unlock")
async def unlock_task_solution(task_id: str, authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_student(user)
    tid = str(task_id or "").strip()
    if not tid:
        raise HTTPException(status_code=400, detail="缺少task_id")

    uid = str(user["id"])
    cost = 20
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT t.id, t.solution_code
        FROM class_members m
        JOIN checkin_tasks t ON t.class_id = m.class_id
        WHERE m.student_id = ? AND t.id = ?
        LIMIT 1
        """,
        (uid, tid)
    )
    task = cur.fetchone()
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="任务不存在或无权限")
    try:
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            "SELECT 1 FROM solution_unlocks WHERE user_id = ? AND kind = 'task' AND key = ? LIMIT 1",
            (uid, tid)
        )
        if cur.fetchone():
            cur.execute("SELECT COALESCE(SUM(change), 0) FROM points_logs WHERE user_id = ?", (uid,))
            total = int(cur.fetchone()[0] or 0)
            conn.commit()
            conn.close()
            return {"success": True, "unlocked": True, "solutionCode": str(task["solution_code"] or ""), "points": max(total, 0)}

        cur.execute("SELECT COALESCE(SUM(change), 0) FROM points_logs WHERE user_id = ?", (uid,))
        total = int(cur.fetchone()[0] or 0)
        if total < 0:
            total = 0
        if total < cost:
            conn.rollback()
            conn.close()
            return {"success": False, "message": "积分不足"}

        cur.execute(
            "INSERT OR IGNORE INTO solution_unlocks (user_id, kind, key) VALUES (?, 'task', ?)",
            (uid, tid)
        )
        _add_points(cur, uid, -cost, "solution", f"解锁参考答案：{tid}")
        conn.commit()
        conn.close()
        return {"success": True, "unlocked": True, "solutionCode": str(task["solution_code"] or ""), "points": total - cost}
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        return {"success": False, "message": "解锁失败"}

def _submission_exercise(row):
    try:
        metadata = json.loads(row["exercise_metadata"] or "{}")
        return metadata if isinstance(metadata, dict) else {}
    except (TypeError, ValueError, KeyError, IndexError):
        return {}


@app.get("/api/student/wrong-questions")
async def list_student_wrong_questions(authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_student(user)
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    try:
        # Get the actual latest failed attempt, including its code and error,
        # rather than mixing arbitrary columns from a grouped SQLite query.
        wrong_rows = conn.execute("""
            SELECT s.*, grouped.error_count
            FROM code_submissions s JOIN (
                SELECT problem_id, language, COUNT(*) AS error_count, MAX(id) AS latest_id
                FROM code_submissions
                WHERE student_id = ? AND success = 0 AND COALESCE(problem_id, '') != ''
                GROUP BY problem_id, language
            ) grouped ON s.id = grouped.latest_id
            ORDER BY s.id DESC LIMIT 200
        """, (user["id"],)).fetchall()
        teacher_rows = conn.execute("""
            SELECT t.*, EXISTS (
                SELECT 1 FROM solution_unlocks u
                WHERE u.user_id = ? AND u.kind = 'task' AND u.key = t.id
            ) AS solution_unlocked
            FROM class_members m JOIN checkin_tasks t ON t.class_id = m.class_id
            WHERE m.student_id = ?
        """, (user["id"], user["id"])).fetchall()
    finally:
        conn.close()
    teacher_map = {str(row["id"]): dict(row) for row in teacher_rows}
    labels = {"javascript": "JavaScript", "python": "Python", "java": "Java", "c": "C"}
    questions = {}
    for row in wrong_rows:
        metadata = _submission_exercise(row)
        problem_id = str(row["problem_id"])
        task_id = problem_id[5:] if problem_id.startswith("task-") else problem_id
        task = teacher_map.get(task_id)
        if task and task["language"] != row["language"]:
            task = None
        canonical_id = f"task-{task_id}" if task else problem_id
        key = (canonical_id, row["language"])
        if key in questions:
            questions[key]["errorCount"] += int(row["error_count"] or 0)
            continue
        topic = _classify_knowledge_point(row["error"], row["code"])
        questions[key] = {
            "problem_id": canonical_id,
            "language": row["language"],
            "languageLabel": labels.get(row["language"], row["language"]),
            "errorCount": int(row["error_count"] or 0),
            "latestErrorAt": row["created_at"],
            "latestError": row["error"] or "",
            "lastCode": row["code"] or "",
            "inputData": row["input_data"] or "",
            "hasQuestionMetadata": bool(task or metadata.get("title")),
            "title": task["title"] if task else (metadata.get("title") or ("自由练习" if problem_id == "sandbox" else f"错题 {problem_id}")),
            "description": task["description"] if task else str(metadata.get("description") or ""),
            "topics": list(dict.fromkeys([str(metadata.get("topic") or ""), topic])) if metadata.get("topic") else [topic],
            "starterCode": task["starter_code"] if task else str(metadata.get("starterCode") or ""),
            "expectedOutput": task["expected_output"] if task else str(metadata.get("expectedOutput") or ""),
            "solutionCode": (task["solution_code"] or "") if task and task["solution_unlocked"] else "",
            "solutionUnlocked": bool(task and task["solution_unlocked"]),
            "taskId": task_id if task else "",
            "isTeacherTask": bool(task),
        }
    return {"success": True, "wrong_questions": sorted(questions.values(), key=lambda item: (-item["errorCount"], item["problem_id"]))}


@app.post("/api/student/practice-results")
async def save_practice_result(req: PracticeResultRequest, authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_student(user)
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM code_submissions WHERE id = ? AND student_id = ?", (req.submission_id, user["id"])).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="运行记录不存在，请先运行当前题目")
        metadata = _submission_exercise(row)
        if "expectedOutput" not in metadata:
            raise HTTPException(status_code=400, detail="这条运行记录缺少题目信息，请重新运行后提交")
        expected = str(metadata.get("expectedOutput") or "").strip()
        if metadata.get("isTeacherTask"):
            task_id = str(metadata.get("taskId") or str(row["problem_id"]).removeprefix("task-"))
            task = conn.execute("""
                SELECT t.expected_output FROM checkin_tasks t
                JOIN class_members m ON m.class_id = t.class_id
                WHERE t.id = ? AND m.student_id = ? AND t.language = ? LIMIT 1
            """, (task_id, user["id"], row["language"])).fetchone()
            if task is None:
                raise HTTPException(status_code=403, detail="当前无权提交这道教师任务")
            expected = str(task["expected_output"] or "").strip()
        actual = str(row["output"] or "").strip()
        runtime_success = bool(metadata.get("runtimeSuccess", row["success"]))
        passed = runtime_success and (not expected or expected in actual)
        error = "" if passed else (str(row["error"] or "") if not runtime_success else f"输出不符合预期：预期包含 {expected!r}，实际输出 {actual!r}")
        metadata["practicePassed"] = passed
        conn.execute("UPDATE code_submissions SET success = ?, error = ?, exercise_metadata = ? WHERE id = ?", (int(passed), error[:20000], json.dumps(metadata, ensure_ascii=False), req.submission_id))
        conn.commit()
        return {"success": True, "passed": passed, "output": row["output"] or "", "expected_output": expected, "error": error}
    finally:
        conn.close()


@app.get("/api/teacher/checkin-status")
async def teacher_checkin_status(class_id: str = "", authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_teacher(user)
    class_id = str(class_id or "").strip()
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if class_id:
        cur.execute("SELECT id FROM classes WHERE id = ? AND teacher_id = ? LIMIT 1", (class_id, user["id"]))
        cls = cur.fetchone()
        if not cls:
            conn.close()
            raise HTTPException(status_code=403, detail="无权限操作该班级")
        cls_ids = [class_id]
    else:
        cur.execute("SELECT id FROM classes WHERE teacher_id = ?", (user["id"],))
        cls_ids = [r["id"] for r in (cur.fetchall() or [])]
    if not cls_ids:
        conn.close()
        return {"success": True, "students": []}
    placeholders = ",".join(["?"] * len(cls_ids))
    cur.execute(
        f"SELECT c.id AS class_id, c.name AS class_name, c.code AS class_code, u.id AS student_id, u.username, u.name, us.daily_checkin "
        f"FROM classes c JOIN class_members m ON m.class_id = c.id "
        f"JOIN users u ON u.id = m.student_id "
        f"LEFT JOIN user_state us ON us.user_id = u.id "
        f"WHERE c.id IN ({placeholders}) ORDER BY c.created_at DESC, u.username ASC",
        tuple(cls_ids)
    )
    rows = cur.fetchall() or []
    conn.close()
    students = []
    for r in rows:
        daily = {}
        try:
            daily = json.loads(r["daily_checkin"] or "{}")
            if not isinstance(daily, dict):
                daily = {}
        except Exception:
            daily = {}
        students.append({
            "class_id": r["class_id"],
            "class_name": r["class_name"],
            "class_code": r["class_code"],
            "student_id": r["student_id"],
            "student_name": r["name"] or r["username"],
            "username": r["username"],
            "last": str(daily.get("last") or ""),
            "streak": int(daily.get("streak") or 0)
        })
    return {"success": True, "students": students}

@app.get("/api/ai/status")
async def ai_status():
    return {
        "doubao_configured": bool(os.environ.get("DOUBAO_API_KEY", "").strip()),
        "deepseek_configured": bool(os.environ.get("DEEPSEEK_API_KEY", "").strip())
    }

def deepseek_analyze_usage(stats: dict) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("missing_api_key")

    base_url = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com").rstrip("/")
    model = deepseek_model()
    url = f"{base_url}/chat/completions"

    prompt = {
        "role": "user",
        "content": (
            "你是编程学习平台的学习分析助手。请根据给定运行统计，输出中文分析，要求：\n"
            "1) 先给出一句总结（<=30字）；\n"
            "2) 再给出 3-6 条可执行建议（用 - 开头）；\n"
            "3) 如有主要错误类型，解释其常见原因与修复方向；\n"
            "4) 内容简洁，避免空话。\n\n"
            f"统计数据（JSON）：\n{json.dumps(stats or {}, ensure_ascii=False)}"
        )
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是严谨的中文学习分析助手。"},
            prompt
        ],
        "temperature": 0.2,
        "max_tokens": 700,
        "stream": False
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
            data = json.loads(raw or "{}")
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="ignore")
        except Exception:
            detail = ""
        raise RuntimeError(f"http_error:{e.code}:{detail}") from e
    except Exception as e:
        raise RuntimeError("network_error") from e

    content = ""
    try:
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    except Exception:
        content = ""
    content = str(content).strip()
    if not content:
        raise RuntimeError("empty_response")
    return content

@app.post("/api/ai/chat")
async def ai_chat(request: ChatRequest):
    try:
        async with httpx.AsyncClient(timeout=65) as client:
            response = await client.post(os.environ.get("AI_SERVICE_URL", "http://127.0.0.1:3000").rstrip("/") + "/api/ai/chat", json=request.model_dump() if hasattr(request,"model_dump") else request.dict())
            return response.json()
    except (httpx.HTTPError, ValueError):
        return {"success": False, "code": "NETWORK_ERROR", "message": "编程助手暂时无法连接，请稍后重试。"}

@app.post("/api/ai/auto-review")
async def ai_auto_review(req: AutoReviewRequest):
    lang = str(req.language or "").strip().lower()
    code = str(req.code or "")
    err = str(req.error or "")
    expected = str(req.expected_output or "")
    topic = _classify_knowledge_point(err, code)

    def _extract_line(text: str):
        s = str(text or "")
        m = re.search(r"line\s+(\d+)", s, flags=re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None
        m = re.search(r":(\d+):(\d+)", s)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None
        return None

    line_no = _extract_line(err)
    loc = f"先定位报错行：第 {line_no} 行附近逐行检查。" if line_no else "先定位报错信息里的行号/位置，然后从该行附近逐行检查。"

    quick_lines = []
    quick_lines.append("我检测到本次运行失败，给你一个快速排查路径：")
    quick_lines.append(f"1) {loc}")
    quick_lines.append(f"2) 错误类型倾向：{topic}。")

    if topic == "语法与标点":
        quick_lines.append("3) 检查括号/引号/逗号/分号是否成对，函数/类/代码块是否闭合。")
    elif topic == "缩进与代码块":
        quick_lines.append("3) 检查缩进层级是否一致（不要混用 Tab/空格），以及 if/for/def 后面是否有缩进代码块。")
    elif topic == "变量/作用域/未定义":
        quick_lines.append("3) 检查变量名拼写、作用域、是否先定义再使用；循环变量/函数名是否写错。")
    elif topic == "类型与转换":
        quick_lines.append("3) 检查传入数据类型，字符串/数字是否混用；需要时显式转换类型并打印变量查看。")
    elif topic == "空值/空指针":
        quick_lines.append("3) 检查对象/数组是否为 null/undefined/None；先判空再访问属性或下标。")
    elif topic == "数组/下标与越界":
        quick_lines.append("3) 检查下标边界：循环条件用 < length，访问前先判断长度。")
    elif topic == "输入输出与解析":
        quick_lines.append("3) 检查输入格式与解析逻辑是否一致；处理空输入/多行输入，必要时打印读到的内容。")
    elif topic == "编译与构建":
        quick_lines.append("3) 先让代码能通过编译：缺少分号/头文件/类名/主函数等，再看运行逻辑。")
    elif topic == "依赖/环境配置":
        quick_lines.append("3) 检查是否缺少依赖/运行环境；确认语言版本与库是否可用。")
    elif topic == "超时/死循环/复杂度":
        quick_lines.append("3) 检查是否死循环/递归无终止；优化算法复杂度，减少重复计算。")
    else:
        quick_lines.append("3) 如果不是语法问题，重点检查边界条件与输出格式是否符合要求。")

    if expected:
        quick_lines.append("补充：如果是输出不符合预期，先对照预期输出，确认多余空格/换行与格式。")

    quick = "\n".join(quick_lines).strip()

    ai_reply, provider = "", "local"
    if os.environ.get("DOUBAO_API_KEY", "").strip() or os.environ.get("DEEPSEEK_API_KEY", "").strip() or os.environ.get("AI_CHAT_COMPLETIONS_URL", "").strip():
        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                response = await client.post(os.environ.get("AI_SERVICE_URL", "http://127.0.0.1:3000").rstrip("/") + "/api/ai/chat", json={
                    "message": "请针对这次错误给出简短排查步骤，不要给出完整答案。",
                    "context": {"mode": "practice", "language": lang, "code": code[:6500], "error": err[:2000]}})
                data = response.json()
                if response.is_success and data.get("success"):
                    ai_reply, provider = str(data.get("reply") or ""), str(data.get("provider") or "AI")
        except (httpx.HTTPError, ValueError):
            pass
    return {"success": True, "quick": quick, "ai": ai_reply, "provider": provider, "topic": topic}

# ====================== JavaScript 运行逻辑（保持正常） ======================
def run_js_code(code: str, input_str: str = ""):
    try:
        input_data = input_str + "\n" if input_str else "\n"
        result = subprocess.run(
            ["node", "-e", code],
            input=input_data,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20
        )
        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""
        
        if result.returncode == 0:
            return {"success": True, "output": stdout or "JS 运行成功，无输出内容"}
        else:
            return {"success": False, "error": stderr or "JS 运行未知错误"}
    except FileNotFoundError:
        return {"success": False, "error": "未检测到 Node.js，请先安装 Node.js 环境"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "JS 运行超时（超过20秒）"}
    except Exception as e:
        return {"success": False, "error": f"JS 运行系统异常：{str(e)}"}

# ====================== Python 运行逻辑（保持正常） ======================
def run_python_code(code: str, input_str: str = ""):
    try:
        env = os.environ.copy()
        if sys.platform == "win32":
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"
            env["PYTHONLEGACYWINDOWSSTDIO"] = "1"
        input_data = input_str + "\n" if input_str else "\n"
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py", encoding="utf-8") as f:
                f.write(code)
                tmp_path = f.name
            result = subprocess.run(
                [sys.executable, "-X", "utf8", tmp_path],
                input=input_data,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                env=env
            )
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        
        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""
        
        if result.returncode == 0:
            return {"success": True, "output": stdout or "Python 运行成功，无输出内容"}
        else:
            return {"success": False, "error": stderr or "Python 运行未知错误"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Python 运行超时（超过10秒）"}
    except Exception as e:
        return {"success": False, "error": f"系统异常：{str(e)}"}

# ====================== Java 运行逻辑（终极稳定版，无乱码、无多余输出） ======================
def run_java_code(code: str, input_str: str = ""):
    try:
        # 1. 提取类名
        class_pattern = re.compile(r'(?:public\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{', re.MULTILINE)
        class_match = class_pattern.search(code)
        if not class_match:
            return {"success": False, "error": "未检测到有效类名（需包含 class 定义，类名以字母/下划线开头）"}
        class_name = class_match.group(1)

        # 2. 临时目录（避免权限问题）
        with tempfile.TemporaryDirectory() as temp_dir:
            java_file_path = os.path.join(temp_dir, f"{class_name}.java")
            
            # 3. 写入文件：强制 UTF-8（保证文件本身无乱码）
            with open(java_file_path, "w", encoding="utf-8") as f:
                f.write(code)

            # 4. 编译：仅强制 UTF-8 编码，不用 cmd 切换编码（关键！）
            compile_cmd = ["javac", "-encoding", "UTF-8", java_file_path]
            compile_result = subprocess.run(
                compile_cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                encoding="gbk",  # Windows 下编译错误用 GBK 解码
                errors="replace",
                timeout=20,
                shell=False
            )
            
            # 处理编译错误
            compile_error = (compile_result.stdout + compile_result.stderr).strip()
            if compile_result.returncode != 0:
                return {"success": False, "error": f"Java 编译失败：{compile_error or '无具体错误信息'}"}

            # 5. 运行：仅指定编码，不用 cmd 封装，不用 chcp（关键！）
            run_cmd = ["java", "-Dfile.encoding=GBK", class_name]
            input_data = input_str + "\n" if input_str else "\n"
            run_result = subprocess.run(
                run_cmd,
                input=input_data,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                encoding="gbk",  # Windows 下 Java 输出用 GBK 解码（核心修复！）
                errors="replace",
                timeout=20,
                shell=False
            )
            
            # 6. 过滤输出（核心：去掉系统提示 + 空行）
            raw_output = (run_result.stdout + run_result.stderr).strip()
            # 过滤的关键字
            filter_keywords = [
                "Picked up JAVA_TOOL_OPTIONS",
                "Microsoft Windows [Version",
                "Active code page"
            ]
            # 逐行过滤
            final_lines = []
            for line in raw_output.split("\n"):
                line_strip = line.strip()
                # 跳过空行和过滤关键字行
                if not line_strip:
                    continue
                if any(keyword in line_strip for keyword in filter_keywords):
                    continue
                final_lines.append(line_strip)
            final_output = "\n".join(final_lines)

            # 7. 返回结果
            if run_result.returncode != 0:
                return {"success": False, "error": final_output or "Java 运行失败，无错误信息"}
            else:
                return {"success": True, "output": final_output or "Java 运行成功，无输出内容"}
                
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Java 运行/编译超时（超过20秒）"}
    except Exception as e:
        return {"success": False, "error": f"Java 运行系统异常：{str(e)}"}

# ====================== C 运行逻辑 ======================
def run_c_code(code: str, input_str: str = ""):
    try:
        input_data = input_str + "\n" if input_str else "\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            c_file_path = os.path.join(temp_dir, "main.c")
            with open(c_file_path, "w", encoding="utf-8") as f:
                f.write(code)

            exe_name = "a.exe" if sys.platform == "win32" else "a.out"
            exe_path = os.path.join(temp_dir, exe_name)

            compile_cmd = ["gcc", "-std=c11", "-O2", c_file_path, "-o", exe_path]
            try:
                compile_result = subprocess.run(
                    compile_cmd,
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=20,
                    shell=False
                )
            except FileNotFoundError:
                return {"success": False, "error": "未检测到 C 编译器 gcc：请安装 MinGW-w64（Windows）或 gcc（Linux/macOS）"}

            compile_output = (compile_result.stdout or "") + (compile_result.stderr or "")
            if compile_result.returncode != 0:
                return {"success": False, "error": f"C 编译失败：{compile_output.strip() or '无具体错误信息'}"}

            run_result = subprocess.run(
                [exe_path],
                cwd=temp_dir,
                input=input_data,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                shell=False
            )

            stdout = (run_result.stdout or "").strip()
            stderr = (run_result.stderr or "").strip()
            if run_result.returncode != 0:
                return {"success": False, "error": stderr or stdout or "C 运行失败，无错误信息"}
            return {"success": True, "output": stdout or "C 运行成功，无输出内容"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "C 运行/编译超时"}
    except Exception as e:
        return {"success": False, "error": f"C 运行系统异常：{str(e)}"}

# ====================== 核心接口 ======================
@app.post("/api/run-code")
async def run_code(request: CodeRequest):
    lang = request.lang
    code = request.code
    input_str = request.input

    if not lang or not code:
        raise HTTPException(status_code=400, detail="缺少语言类型或代码内容")

    if lang == "javascript":
        result = run_js_code(code, input_str)
    elif lang == "python":
        result = run_python_code(code, input_str)
    elif lang == "java":
        result = run_java_code(code, input_str)
    elif lang == "c":
        result = run_c_code(code, input_str)
    else:
        raise HTTPException(status_code=400, detail=f"暂不支持 {lang} 语言")

    record_code_submission(request.dict(), {**result, "input": input_str})
    return result


def record_code_submission(request: dict, result: dict):
    conn = None
    try:
        conn = _db_connect()
        cur = conn.cursor()
        raw_metadata = request.get("exercise") or {}
        allowed = ("title", "description", "topic", "difficulty", "starterCode", "expectedOutput", "isTeacherTask", "taskId")
        metadata = {key: raw_metadata[key] for key in allowed if key in raw_metadata} if isinstance(raw_metadata, dict) else {}
        metadata["runtimeSuccess"] = bool(result.get("success"))
        cur.execute(
            "INSERT INTO code_submissions (student_id, student_name, problem_id, code, language, input_data, output, error, success, exercise_metadata) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(request.get("student_id") or "guest"),
                str(request.get("student_name") or "游客"),
                str(request.get("problem_id") or "unknown"),
                str(request.get("code") or ""),
                str(request.get("lang") or ""),
                str(result.get("input") or ""),
                str(result.get("output") or "") if isinstance(result, dict) else "",
                str(result.get("error") or "") if isinstance(result, dict) else "",
                1 if (isinstance(result, dict) and result.get("success")) else 0,
                json.dumps(metadata, ensure_ascii=False)
            )
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        pass
    finally:
        if conn is not None:
            conn.close()

@app.websocket("/api/console")
async def console_endpoint(websocket: WebSocket):
    await run_console(websocket, record_submission=record_code_submission)

def analyze_usage(stats: dict) -> str:
    total = int(stats.get("totalRuns") or 0)
    success = int(stats.get("successRuns") or 0)
    error = int(stats.get("errorRuns") or 0)
    errors = stats.get("errors") or {}
    if not isinstance(errors, dict):
        errors = {}

    top = sorted([(k, int(v or 0)) for k, v in errors.items()], key=lambda x: x[1], reverse=True)
    top = [(k, v) for k, v in top if v > 0][:5]

    lines = []
    lines.append(f"总运行次数：{total} 次")
    lines.append(f"成功：{success} 次，失败：{error} 次")

    if total == 0:
        return "当前没有可供分析的提交记录，请先完成一次编程练习。"
    if error == 0:
        lines.append("近期没有错误记录，建议继续保持；可以尝试提高题目难度或增加边界用例测试。")
        return "\n".join(lines)

    if top:
        lines.append("主要错误类型（Top）：")
        for k, v in top:
            ratio = (v / error) * 100 if error else 0
            lines.append(f"- {k}：{v} 次（{ratio:.1f}%）")
    else:
        lines.append("暂未识别到明确的错误分类。")

    tips = []
    top_type = top[0][0] if top else ""
    if top_type == "SyntaxError":
        tips.append("语法错误占比较高：建议在运行前先检查括号/缩进/引号是否成对，逐行执行定位报错行。")
    if top_type in ("NameError", "ReferenceError"):
        tips.append("变量未定义占比较高：建议先定义再使用，注意作用域与拼写一致。")
    if top_type == "TypeError":
        tips.append("类型错误占比较高：建议打印变量类型，确认传参与返回值符合预期。")
    if top_type == "IndexError":
        tips.append("越界错误占比较高：建议检查数组/列表长度与下标边界，循环条件写成 < length。")
    if top_type == "CompilationError":
        tips.append("编译错误占比较高：建议先保证代码能通过编译，再考虑运行逻辑；检查缺少分号/头文件/类名等。")
    if top_type == "Timeout":
        tips.append("超时占比较高：建议优化算法复杂度，避免死循环，必要时加入终止条件。")

    if tips:
        lines.append("改进建议：")
        lines.extend([f"- {t}" for t in tips])

    lines.append("你可以在“首页代码编辑器”多做几次运行，系统会持续更新占比并给出更贴合的建议。")
    return "\n".join(lines)

@app.post("/api/ai/analyze")
async def ai_analyze(request: AnalyzeRequest, fast: bool = Query(False), prefer: str = Query("auto")):
    try:
        stats = request.stats or {}

        if fast or prefer == "local":
            return {"success": True, "provider": "local", "analysis": analyze_usage(stats)}

        deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if prefer == "deepseek" and not deepseek_key:
            return {"success": True, "provider": "local", "analysis": analyze_usage(stats), "fallback_reason": "missing_api_key"}

        if deepseek_key:
            try:
                analysis = await asyncio.wait_for(asyncio.to_thread(deepseek_analyze_usage, stats), timeout=32)
                return {"success": True, "provider": "deepseek", "analysis": analysis}
            except (RuntimeError, asyncio.TimeoutError) as e:
                reason = "timeout" if isinstance(e, asyncio.TimeoutError) else str(e)
                if reason.startswith("http_error:"):
                    reason = "http_error"
                return {"success": True, "provider": "local", "analysis": analyze_usage(stats), "fallback_reason": reason}

        return {"success": True, "provider": "local", "analysis": analyze_usage(stats), "fallback_reason": "missing_api_key"}
    except Exception:
        return {"success": False, "message": "分析失败"}

@app.get("/api/analysis/{student_id}")
async def get_analysis(student_id: str):
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) as total, SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count, "
        "COUNT(DISTINCT problem_id) as problems_attempted, "
        "COUNT(DISTINCT CASE WHEN success = 1 THEN problem_id ELSE NULL END) as passed_unique "
        "FROM code_submissions WHERE student_id = ?",
        (student_id,)
    )
    row = cur.fetchone() or (0, 0, 0, 0)
    conn.close()
    total = int(row[0] or 0)
    success_count = int(row[1] or 0)
    return {
        "student_id": student_id,
        "total_submissions": total,
        "success_count": success_count,
        "success_rate": round(success_count / total * 100, 2) if total > 0 else 0,
        "problems_attempted": int(row[2] or 0),
        "passed_unique": int(row[3] or 0)
    }

@app.get("/api/analysis/language/{student_id}")
async def get_language_stats(student_id: str):
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT language, COUNT(*) as total, SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count "
        "FROM code_submissions WHERE student_id = ? GROUP BY language ORDER BY total DESC",
        (student_id,)
    )
    rows = cur.fetchall() or []
    conn.close()
    language_stats = []
    for r in rows:
        total = int(r[1] or 0)
        success = int(r[2] or 0)
        language_stats.append({
            "language": r[0],
            "total": total,
            "success": success,
            "fail": total - success,
            "success_rate": round(success / total * 100, 2) if total > 0 else 0
        })
    return {"student_id": student_id, "language_stats": language_stats}

def _classify_knowledge_point(error_text: str, code_text: str) -> str:
    text = f"{error_text or ''}\n{code_text or ''}"
    t = text.lower()
    rules = [
        ("依赖/环境配置", r"(modulenotfounderror|no module named|cannot find symbol|package .* does not exist|classnotfoundexception|command not found|未检测到|环境|依赖)"),
        ("编译与构建", r"(compilation|编译失败|javac|gcc|ld\.exe|undefined reference|linker|\serror:\s)"),
        ("语法与标点", r"(syntaxerror|invalid syntax|unexpected token|expected ';'|missing ';'|unterminated|missing \)|missing \]|missing \})"),
        ("缩进与代码块", r"(indentationerror|unexpected indent|expected an indented block)"),
        ("变量/作用域/未定义", r"(nameerror|referenceerror|is not defined|undeclared identifier|cannot find variable)"),
        ("类型与转换", r"(typeerror|classcastexception|numberformatexception|cannot convert|incompatible types|unsupported operand|invalid literal)"),
        ("空值/空指针", r"(nullpointerexception|nonetype|cannot read properties of null|cannot read properties of undefined|null reference)"),
        ("数组/下标与越界", r"(indexerror|out of range|arrayindexoutofboundsexception|segmentation fault|access violation)"),
        ("输入输出与解析", r"(eoferror|input\(|scanf|printf|valueerror|invalid input|could not convert)"),
        ("递归/栈溢出", r"(recursionerror|stack overflow)"),
        ("超时/死循环/复杂度", r"(timeout|timed out|超时|time limit)"),
    ]
    for topic, pattern in rules:
        try:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return topic
        except Exception:
            continue
    if "assert" in t or "assertion" in t:
        return "断言/测试用例"
    if "exception" in t or "traceback" in t:
        return "异常处理"
    return "逻辑/输出不符合预期"

# 新增@app.get("/api/history/{student_id}")
async def get_history(student_id: str, problem_id: str = None):
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    if problem_id:
        cur.execute('''
            SELECT id, student_name, code, language, success, output, error, created_at
            FROM code_submissions
            WHERE student_id = ? AND problem_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        ''', (student_id, problem_id))
        
        rows = cur.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "id": row["id"],
                "student_name": row["student_name"],
                "code": row["code"],
                "language": row["language"],
                "success": bool(row["success"]),
                "output": row["output"],
                "error": row["error"],
                "submitted_at": row["created_at"]
            })
    else:
        cur.execute('''
            SELECT id, student_name, problem_id, code, language, success, output, error, created_at
            FROM code_submissions
            WHERE student_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        ''', (student_id,))
        
        rows = cur.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "id": row["id"],
                "student_name": row["student_name"],
                "problem_id": row["problem_id"],
                "code": row["code"],
                "language": row["language"],
                "success": bool(row["success"]),
                "output": row["output"],
                "error": row["error"],
                "submitted_at": row["created_at"]
            })
    
    return {"student_id": student_id, "history": history}
@app.get("/api/history/{student_id}")
async def get_history(student_id: str, problem_id: str = None):
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    if problem_id:
        cur.execute('''
            SELECT id, student_name, code, language, success, output, error, created_at
            FROM code_submissions
            WHERE student_id = ? AND problem_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        ''', (student_id, problem_id))
        
        rows = cur.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "id": row["id"],
                "student_name": row["student_name"],
                "code": row["code"],
                "language": row["language"],
                "success": bool(row["success"]),
                "output": row["output"],
                "error": row["error"],
                "submitted_at": row["created_at"]
            })
    else:
        cur.execute('''
            SELECT id, student_name, problem_id, code, language, success, output, error, created_at
            FROM code_submissions
            WHERE student_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        ''', (student_id,))
        
        rows = cur.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "id": row["id"],
                "student_name": row["student_name"],
                "problem_id": row["problem_id"],
                "code": row["code"],
                "language": row["language"],
                "success": bool(row["success"]),
                "output": row["output"],
                "error": row["error"],
                "submitted_at": row["created_at"]
            })
    
    return {"student_id": student_id, "history": history}

@app.get("/api/analysis/knowledge/{student_id}")
async def get_knowledge_stats(student_id: str, limit: int = 200):
    lim = int(limit or 200)
    if lim <= 0:
        lim = 200
    if lim > 500:
        lim = 500

    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) AS total, SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) AS err_total "
        "FROM code_submissions WHERE student_id = ?",
        (student_id,)
    )
    row = cur.fetchone() or {}
    total = int(row["total"] or 0)
    err_total = int(row["err_total"] or 0)

    cur.execute(
        "SELECT problem_id, code, error, created_at FROM code_submissions "
        "WHERE student_id = ? AND success = 0 ORDER BY created_at DESC LIMIT ?",
        (student_id, lim)
    )
    rows = cur.fetchall() or []
    conn.close()

    buckets = {}
    examples = {}
    for r in rows:
        err = str(r["error"] or "")
        code = str(r["code"] or "")
        topic = _classify_knowledge_point(err, code)
        buckets[topic] = buckets.get(topic, 0) + 1
        if topic not in examples:
            examples[topic] = {
                "problem_id": str(r["problem_id"] or ""),
                "error": (err[:240] + "…") if len(err) > 240 else err
            }
    topics = sorted(buckets.items(), key=lambda x: x[1], reverse=True)
    out = []
    for topic, count in topics:
        ratio = round((count / err_total) * 100, 2) if err_total > 0 else 0
        out.append({"topic": topic, "count": count, "ratio": ratio, "example": examples.get(topic)})
    return {"student_id": student_id, "total_submissions": total, "error_submissions": err_total, "knowledge_points": out}
# ====================== 错题本接口 ======================

# 注意：具体路径放在前面！
@app.get("/api/wrong-questions/statistics/{student_id}")
async def get_wrong_statistics(student_id: str):
    """获取错题统计（按知识点分类、按语言分类）"""
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # 按题目统计错题次数
    cur.execute("""
        SELECT problem_id, COUNT(*) as wrong_count, 
               MAX(created_at) as last_wrong
        FROM code_submissions
        WHERE student_id = ? AND success = 0
        GROUP BY problem_id
        ORDER BY wrong_count DESC
        LIMIT 20
    """, (student_id,))
    
    problem_stats = []
    for row in cur.fetchall():
        problem_stats.append({
            "problem_id": row["problem_id"],
            "wrong_count": row["wrong_count"],
            "last_wrong": row["last_wrong"]
        })
    
    # 按语言统计错题
    cur.execute("""
        SELECT language, COUNT(*) as wrong_count
        FROM code_submissions
        WHERE student_id = ? AND success = 0
        GROUP BY language
        ORDER BY wrong_count DESC
    """, (student_id,))
    
    language_stats = []
    for row in cur.fetchall():
        language_stats.append({
            "language": row["language"],
            "wrong_count": row["wrong_count"]
        })
    
    # 总数统计
    cur.execute("""
        SELECT COUNT(*) as total_wrong,
               COUNT(DISTINCT problem_id) as distinct_problems
        FROM code_submissions
        WHERE student_id = ? AND success = 0
    """, (student_id,))
    
    total_row = cur.fetchone()
    conn.close()
    
    return {
        "success": True,
        "total_wrong": total_row["total_wrong"] if total_row else 0,
        "distinct_problems": total_row["distinct_problems"] if total_row else 0,
        "problem_stats": problem_stats,
        "language_stats": language_stats
    }


@app.get("/api/wrong-questions/{student_id}")
async def get_wrong_questions(
    student_id: str, 
    limit: int = 50,
    problem_id: str = None,
    language: str = None
):
    """获取学生的错题列表"""
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    sql = """
        SELECT id, student_name, problem_id, code, language, 
               input_data, output, error, created_at
        FROM code_submissions
        WHERE student_id = ? AND success = 0
    """
    params = [student_id]
    
    if problem_id:
        sql += " AND problem_id = ?"
        params.append(problem_id)
    
    if language:
        sql += " AND language = ?"
        params.append(language)
    
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    
    wrong_questions = []
    for row in rows:
        wrong_questions.append({
            "id": row["id"],
            "student_name": row["student_name"],
            "problem_id": row["problem_id"],
            "code": row["code"],
            "language": row["language"],
            "input_data": row["input_data"] or "",
            "output": row["output"] or "",
            "error": row["error"] or "",
            "submitted_at": row["created_at"]
        })
    
    return {"success": True, "wrong_questions": wrong_questions, "total": len(wrong_questions)}


@app.delete("/api/wrong-questions/{question_id}")
async def delete_wrong_question(question_id: int, authorization: str = Header(None)):
    """删除错题记录"""
    user = _require_user(authorization)
    
    conn = _db_connect()
    cur = conn.cursor()
    
    cur.execute(
        "DELETE FROM code_submissions WHERE id = ? AND student_id = ? AND success = 0",
        (question_id, user["id"])
    )
    conn.commit()
    affected = cur.rowcount
    conn.close()
    
    if affected == 0:
        raise HTTPException(status_code=404, detail="错题不存在或无权限删除")
    
    return {"success": True, "message": "删除成功"}

# ====================== 测试 API ======================
def _parse_time_range(text: str):
    s = str(text or "").strip()
    if not s:
        return None, None
    parts = re.split(r"\s*[~～]\s*", s)
    if len(parts) != 2:
        return None, None

    left = str(parts[0] or "").strip()
    right = str(parts[1] or "").strip()
    if not left or not right:
        return None, None

    year = datetime.now().year

    def _parse_piece(piece: str):
        p = str(piece or "").strip().replace("/", "-")
        if not p:
            return None, None, False
        try:
            if re.match(r"^\d{4}-\d{2}-\d{2}$", p):
                dt = datetime.strptime(p, "%Y-%m-%d")
                return dt, {"has_date": True, "has_time": False}, True
            if re.match(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}$", p):
                dt = datetime.strptime(p, "%Y-%m-%d %H:%M")
                return dt, {"has_date": True, "has_time": True}, True
            if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$", p):
                dt = datetime.fromisoformat(p)
                return dt, {"has_date": True, "has_time": True}, True
            if re.match(r"^\d{2}-\d{2}$", p):
                dt = datetime.strptime(f"{year}-{p}", "%Y-%m-%d")
                return dt, {"has_date": True, "has_time": False}, True
            if re.match(r"^\d{2}-\d{2}\s+\d{2}:\d{2}$", p):
                dt = datetime.strptime(f"{year}-{p}", "%Y-%m-%d %H:%M")
                return dt, {"has_date": True, "has_time": True}, True
            if re.match(r"^\d{2}:\d{2}$", p):
                t = datetime.strptime(p, "%H:%M")
                return t, {"has_date": False, "has_time": True}, True
        except Exception:
            return None, None, False
        return None, None, False

    start_dt, start_meta, ok1 = _parse_piece(left)
    end_dt, end_meta, ok2 = _parse_piece(right)
    if not ok1 or not ok2 or start_dt is None or end_dt is None:
        return None, None

    if start_meta.get("has_date") and (not end_meta.get("has_date")) and end_meta.get("has_time"):
        end_dt = datetime(
            start_dt.year,
            start_dt.month,
            start_dt.day,
            end_dt.hour,
            end_dt.minute,
            0
        )
        end_meta = {"has_date": True, "has_time": True}

    if start_meta.get("has_date") and end_meta.get("has_date"):
        if (not start_meta.get("has_time")) and (not end_meta.get("has_time")):
            end_dt = end_dt + timedelta(days=1) - timedelta(seconds=1)
        return start_dt, end_dt

    return None, None

def _time_window_state(now: datetime, start: datetime, end: datetime):
    if not start or not end:
        return {"valid": False}
    if now < start:
        return {"valid": True, "in": False, "reason": "not_started", "start": start, "end": end}
    if now > end:
        return {"valid": True, "in": False, "reason": "ended", "start": start, "end": end}
    return {"valid": True, "in": True, "reason": "in", "start": start, "end": end}

def _competition_access_meta(register_time: str, competition_time: str):
    now = datetime.now()
    reg_s, reg_e = _parse_time_range(register_time)
    comp_s, comp_e = _parse_time_range(competition_time)
    reg_state = _time_window_state(now, reg_s, reg_e) if reg_s and reg_e else {"valid": False}
    comp_state = _time_window_state(now, comp_s, comp_e) if comp_s and comp_e else {"valid": False}
    can_register = bool(reg_state.get("valid") and reg_state.get("in"))
    can_enter = bool(comp_state.get("valid") and comp_state.get("in"))
    return {
        "canRegister": can_register,
        "canEnter": can_enter,
        "registerStart": reg_s.isoformat(sep=" ") if reg_s else "",
        "registerEnd": reg_e.isoformat(sep=" ") if reg_e else "",
        "competitionStart": comp_s.isoformat(sep=" ") if comp_s else "",
        "competitionEnd": comp_e.isoformat(sep=" ") if comp_e else "",
        "registerValid": bool(reg_state.get("valid")),
        "competitionValid": bool(comp_state.get("valid")),
        "registerReason": str(reg_state.get("reason") or ""),
        "competitionReason": str(comp_state.get("reason") or "")
    }

@app.get("/api/competitions")
async def get_competitions(status: str = None, search: str = None):
    """获取测试列表"""
    # 初始化示例数据（如果是空表）
    _init_sample_competitions()
    
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    query = (
        "SELECT c.*, "
        "(SELECT COUNT(*) FROM competition_problems p WHERE p.competition_id = c.id) AS problem_count "
        "FROM competitions c WHERE 1=1"
    )
    params = []
    
    if status and status != "all":
        query += " AND status = ?"
        params.append(status)
    
    if search:
        query += " AND (name LIKE ? OR desc LIKE ? OR tags LIKE ?)"
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern, search_pattern])
    
    query += " ORDER BY created_at DESC"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    
    competitions = []
    for row in rows:
        # 解析字段（支持逗号分隔或JSON数组）
        tags = []
        if row["tags"]:
            if row["tags"].startswith("[") and row["tags"].endswith("]"):
                try:
                    tags = json.loads(row["tags"])
                except:
                    tags = row["tags"].split(",")
            else:
                tags = row["tags"].split(",")
        
        rules = []
        if row["rules"]:
            if row["rules"].startswith("[") and row["rules"].endswith("]"):
                try:
                    rules = json.loads(row["rules"])
                except:
                    rules = row["rules"].split(",")
            else:
                rules = row["rules"].split(",")
        
        rewards = []
        if row["rewards"]:
            if row["rewards"].startswith("[") and row["rewards"].endswith("]"):
                try:
                    rewards = json.loads(row["rewards"])
                except:
                    rewards = row["rewards"].split(",")
            else:
                rewards = row["rewards"].split(",")
        
        competitions.append({
            "id": row["id"],
            "teacherId": row["teacher_id"] if "teacher_id" in row.keys() else "",
            "name": row["name"],
            "desc": row["desc"],
            "type": row["type"],
            "mode": row["mode"] if "mode" in row.keys() else "general",
            "status": row["status"],
            "difficulty": row["difficulty"],
            "participants": row["participants"],
            "duration": row["duration"],
            "registerTime": row["register_time"],
            "competitionTime": row["competition_time"],
            "tags": tags,
            "detailDesc": row["detail_desc"],
            "rules": rules,
            "rewards": rewards,
            "problemCount": int(row["problem_count"] or 0),
            **_competition_access_meta(str(row["register_time"] or ""), str(row["competition_time"] or ""))
        })
    
    return {"success": True, "data": competitions}

@app.get("/api/competitions/my-registrations")
async def get_my_competition_registrations(authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_student(user)
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT competition_id FROM competition_registrations WHERE user_id = ? ORDER BY registered_at DESC",
        (str(user["id"]),),
    )
    rows = cur.fetchall() or []
    conn.close()
    ids = [int(r[0]) for r in rows if r and str(r[0]).strip()]
    return {"success": True, "competitionIds": ids}

@app.get("/api/competitions/{competition_id}")
async def get_competition_detail(competition_id: int):
    cid = int(competition_id or 0)
    if cid <= 0:
        raise HTTPException(status_code=400, detail="参数不合法")
    _init_sample_competitions()
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT c.*, (SELECT COUNT(*) FROM competition_problems p WHERE p.competition_id = c.id) AS problem_count "
        "FROM competitions c WHERE c.id = ? LIMIT 1",
        (cid,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="测试不存在")

    tags = []
    if row["tags"]:
        if row["tags"].startswith("[") and row["tags"].endswith("]"):
            try:
                tags = json.loads(row["tags"])
            except Exception:
                tags = row["tags"].split(",")
        else:
            tags = row["tags"].split(",")

    rules = []
    if row["rules"]:
        if row["rules"].startswith("[") and row["rules"].endswith("]"):
            try:
                rules = json.loads(row["rules"])
            except Exception:
                rules = row["rules"].split(",")
        else:
            rules = row["rules"].split(",")

    rewards = []
    if row["rewards"]:
        if row["rewards"].startswith("[") and row["rewards"].endswith("]"):
            try:
                rewards = json.loads(row["rewards"])
            except Exception:
                rewards = row["rewards"].split(",")
        else:
            rewards = row["rewards"].split(",")

    comp = {
        "id": row["id"],
        "teacherId": row["teacher_id"] if "teacher_id" in row.keys() else "",
        "name": row["name"],
        "desc": row["desc"],
        "type": row["type"],
        "mode": row["mode"] if "mode" in row.keys() else "general",
        "status": row["status"],
        "difficulty": row["difficulty"],
        "participants": row["participants"],
        "duration": row["duration"],
        "registerTime": row["register_time"],
        "competitionTime": row["competition_time"],
        "tags": tags,
        "detailDesc": row["detail_desc"],
        "rules": rules,
        "rewards": rewards,
        "problemCount": int(row["problem_count"] or 0),
    }
    comp.update(_competition_access_meta(str(row["register_time"] or ""), str(row["competition_time"] or "")))
    return {"success": True, "data": comp}

@app.get("/api/competitions/{competition_id}/problems")
async def get_competition_problems(competition_id: int, authorization: str = Header(None)):
    cid = int(competition_id or 0)
    if cid <= 0:
        raise HTTPException(status_code=400, detail="参数不合法")
    user = _require_user(authorization)
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, status, register_time, competition_time FROM competitions WHERE id = ? LIMIT 1", (cid,))
    c_row = cur.fetchone()
    if not c_row:
        conn.close()
        raise HTTPException(status_code=404, detail="测试不存在")
    if (user or {}).get("role") == "student":
        if str(c_row["status"] or "") == "ended":
            conn.close()
            raise HTTPException(status_code=403, detail="测试已结束，暂不可进入")
        cur.execute(
            "SELECT 1 FROM competition_registrations WHERE competition_id = ? AND user_id = ? LIMIT 1",
            (cid, str(user["id"])),
        )
        if not cur.fetchone():
            conn.close()
            raise HTTPException(status_code=403, detail="请先报名后再进入比赛")
        meta = _competition_access_meta(str(c_row["register_time"] or ""), str(c_row["competition_time"] or ""))
        if meta.get("competitionValid") and (not meta.get("canEnter")):
            reason = str(meta.get("competitionReason") or "")
            if reason == "not_started":
                conn.close()
                raise HTTPException(status_code=403, detail="未到作答时间，暂不可进入比赛")
            if reason == "ended":
                conn.close()
                raise HTTPException(status_code=403, detail="作答时间已结束，暂不可进入比赛")
            conn.close()
            raise HTTPException(status_code=403, detail="暂不可进入比赛")
    cur.execute(
        "SELECT p.task_id, p.category, p.points, p.sort, "
        "t.title, t.description, t.language, t.class_id, t.starter_code, t.expected_output, t.solution_code "
        "FROM competition_problems p "
        "JOIN checkin_tasks t ON t.id = p.task_id "
        "WHERE p.competition_id = ? "
        "ORDER BY p.sort ASC, p.id ASC",
        (cid,),
    )
    rows = cur.fetchall() or []
    conn.close()
    is_student = str((user or {}).get("role") or "") == "student"
    out = []
    for r in rows:
        out.append({
            "taskId": r["task_id"],
            "title": r["title"],
            "description": r["description"] or "",
            "language": r["language"],
            "classId": r["class_id"],
            "category": r["category"] or "",
            "points": int(r["points"] or 0),
            "sort": int(r["sort"] or 0),
            "starterCode": r["starter_code"] or "",
            "expectedOutput": r["expected_output"] or "",
            "solutionCode": "" if is_student else (r["solution_code"] or "")
        })
    return {"success": True, "problems": out}

@app.get("/api/competitions/{competition_id}/my-submissions")
async def get_my_competition_submissions(competition_id: int, authorization: str = Header(None)):
    cid = int(competition_id or 0)
    if cid <= 0:
        raise HTTPException(status_code=400, detail="参数不合法")
    user = _require_user(authorization)
    _require_student(user)
    uid = str(user["id"])
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT task_id, passed, created_at FROM competition_submissions WHERE competition_id = ? AND user_id = ? ORDER BY created_at DESC",
        (cid, uid)
    )
    rows = cur.fetchall() or []
    conn.close()
    items = []
    for r in rows:
        items.append({
            "taskId": str(r["task_id"] or ""),
            "passed": bool(int(r["passed"] or 0)),
            "submittedAt": str(r["created_at"] or "")
        })
    return {"success": True, "submissions": items}

@app.get("/api/competitions/{competition_id}/my-result")
async def get_my_competition_result(competition_id: int, authorization: str = Header(None)):
    cid = int(competition_id or 0)
    if cid <= 0:
        raise HTTPException(status_code=400, detail="参数不合法")
    user = _require_user(authorization)
    _require_student(user)
    uid = str(user["id"])
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, status FROM competitions WHERE id = ? LIMIT 1", (cid,))
    comp = cur.fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=404, detail="测试不存在")
    if str(comp["status"] or "") != "ended":
        conn.close()
        raise HTTPException(status_code=403, detail="测试未结束，暂不可查看成绩")

    cur.execute(
        "SELECT user_id, user_name, registered_at FROM competition_registrations WHERE competition_id = ? ORDER BY registered_at ASC",
        (cid,)
    )
    regs = cur.fetchall() or []
    if not any(str(r["user_id"] or "") == uid for r in regs):
        conn.close()
        raise HTTPException(status_code=403, detail="未报名该测试，无法查看成绩")

    cur.execute(
        "SELECT task_id, points, sort FROM competition_problems WHERE competition_id = ? ORDER BY sort ASC, created_at ASC",
        (cid,)
    )
    prob_rows = cur.fetchall() or []
    problems = [
        {"task_id": str(r["task_id"] or ""), "points": int(r["points"] or 0)}
        for r in prob_rows
        if str(r["task_id"] or "").strip()
    ]
    max_score = sum(int(p.get("points") or 0) for p in problems)

    cur.execute(
        "SELECT user_id, task_id, passed, score, created_at FROM competition_submissions WHERE competition_id = ?",
        (cid,)
    )
    subs = cur.fetchall() or []
    conn.close()

    sub_map = {}
    sub_time_map = {}
    for s in subs:
        suid = str(s["user_id"] or "")
        tid = str(s["task_id"] or "")
        if not suid or not tid:
            continue
        passed = bool(int(s["passed"] or 0)) if s["passed"] is not None else False
        score = s["score"]
        try:
            score_v = int(score) if score is not None else None
        except Exception:
            score_v = None
        sub_map[(suid, tid)] = {"passed": passed, "score": score_v}
        sub_time_map[(suid, tid)] = str(s["created_at"] or "")

    def _parse_dt(raw: str):
        s = str(raw or "").strip()
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("T", " "))
        except Exception:
            return None

    results = []
    for r in regs:
        ru = str(r["user_id"] or "")
        rn = str(r["user_name"] or "")
        reg_at = _parse_dt(r["registered_at"])
        total = 0
        last_submit = None
        if problems:
            for p in problems:
                tid = p["task_id"]
                points = int(p.get("points") or 0)
                it = sub_map.get((ru, tid)) or {}
                if it.get("score") is not None:
                    total += int(it["score"] or 0)
                else:
                    total += points if bool(it.get("passed")) else 0
                ts = _parse_dt(sub_time_map.get((ru, tid), ""))
                if ts:
                    last_submit = ts if (last_submit is None or ts > last_submit) else last_submit
        tiebreak = last_submit or reg_at or datetime.max
        results.append({"userId": ru, "userName": rn, "score": int(total), "tiebreak": tiebreak})

    results_sorted = sorted(
        results,
        key=lambda x: (-int(x.get("score") or 0), x.get("tiebreak") or datetime.max, str(x.get("userId") or "")),
    )
    ranks = {}
    prev_score = None
    rank = 0
    idx = 0
    for item in results_sorted:
        idx += 1
        sc = int(item.get("score") or 0)
        if prev_score is None or sc != prev_score:
            rank = idx
            prev_score = sc
        ranks[str(item.get("userId") or "")] = rank

    my_item = next((x for x in results_sorted if str(x.get("userId") or "") == uid), None)
    my_score = int(my_item.get("score") or 0) if my_item else 0
    my_rank = int(ranks.get(uid) or 0)
    return {
        "success": True,
        "result": {
            "competitionId": cid,
            "userId": uid,
            "score": my_score,
            "rank": my_rank,
            "totalParticipants": len(results_sorted),
            "maxScore": int(max_score)
        }
    }

@app.post("/api/competitions/{competition_id}/submit")
async def submit_competition_answer(competition_id: int, req: CompetitionSubmitRequest, authorization: str = Header(None)):
    cid = int(competition_id or 0)
    if cid <= 0:
        raise HTTPException(status_code=400, detail="参数不合法")
    user = _require_user(authorization)
    _require_student(user)
    uid = str(user["id"])

    task_id = str(req.task_id or "").strip()
    if not task_id:
        raise HTTPException(status_code=400, detail="缺少task_id")
    code = str(req.code or "")
    if not code.strip():
        raise HTTPException(status_code=400, detail="缺少代码")

    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, status, register_time, competition_time FROM competitions WHERE id = ? LIMIT 1", (cid,))
    c_row = cur.fetchone()
    if not c_row:
        conn.close()
        raise HTTPException(status_code=404, detail="测试不存在")
    if str(c_row["status"] or "") == "ended":
        conn.close()
        raise HTTPException(status_code=403, detail="测试已结束，暂不可提交")

    cur.execute(
        "SELECT 1 FROM competition_registrations WHERE competition_id = ? AND user_id = ? LIMIT 1",
        (cid, uid)
    )
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="请先报名后再提交")

    meta = _competition_access_meta(str(c_row["register_time"] or ""), str(c_row["competition_time"] or ""))
    if meta.get("competitionValid") and (not meta.get("canEnter")):
        reason = str(meta.get("competitionReason") or "")
        conn.close()
        if reason == "not_started":
            raise HTTPException(status_code=403, detail="未到作答时间，暂不可提交")
        if reason == "ended":
            raise HTTPException(status_code=403, detail="作答时间已结束，暂不可提交")
        raise HTTPException(status_code=403, detail="暂不可提交")

    cur.execute(
        "SELECT 1 FROM competition_problems WHERE competition_id = ? AND task_id = ? LIMIT 1",
        (cid, task_id)
    )
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="题目不属于该测试")

    cur.execute(
        "SELECT language, expected_output FROM checkin_tasks WHERE id = ? LIMIT 1",
        (task_id,)
    )
    t_row = cur.fetchone()
    if not t_row:
        conn.close()
        raise HTTPException(status_code=404, detail="题目不存在")

    lang = str(req.language or t_row["language"] or "").strip()
    if not lang:
        lang = str(t_row["language"] or "").strip()
    expected = str(t_row["expected_output"] or "").strip()
    input_data = str(req.input_data or "")

    if lang == "javascript":
        result = run_js_code(code, input_data)
    elif lang == "python":
        result = run_python_code(code, input_data)
    elif lang == "java":
        result = run_java_code(code, input_data)
    elif lang == "c":
        result = run_c_code(code, input_data)
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="语言不支持")

    output = str((result or {}).get("output") or "") if isinstance(result, dict) else ""
    error = str((result or {}).get("error") or "") if isinstance(result, dict) else ""
    ok_run = bool(isinstance(result, dict) and result.get("success"))
    actual = str(output or "").strip()
    passed = bool(ok_run and (not expected or (expected in actual)))

    try:
        cur.execute(
            """
            INSERT INTO competition_submissions (competition_id, task_id, user_id, language, code, input_data, output, error, passed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(competition_id, task_id, user_id) DO UPDATE SET
              language=excluded.language,
              code=excluded.code,
              input_data=excluded.input_data,
              output=excluded.output,
              error=excluded.error,
              passed=excluded.passed,
              created_at=CURRENT_TIMESTAMP
            """,
            (cid, task_id, uid, lang, code, input_data, output, error, 1 if passed else 0)
        )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    conn.close()
    return {"success": True, "passed": passed, "output": output, "error": error}

@app.post("/api/teacher/competitions/publish")
async def publish_competition(req: PublishCompetitionRequest, authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_teacher(user)

    name = str(req.name or "").strip()
    desc = str(req.desc or "").strip()
    if not name or not desc:
        raise HTTPException(status_code=400, detail="缺少测试名称或简介")

    mode = str(getattr(req, "mode", "") or "general").strip()
    if mode not in ("general", "problem_set"):
        mode = "general"

    status = str(req.status or "registering").strip()
    if status not in ("registering", "ongoing", "ended"):
        status = "registering"

    ctype = str(req.type or "algorithm").strip() or "algorithm"
    difficulty = str(req.difficulty or "中等").strip() or "中等"
    duration = str(req.duration or "4小时").strip() or "4小时"
    register_time = str(req.register_time or "").strip()
    competition_time = str(req.competition_time or "").strip()
    detail_desc = str(req.detail_desc or "").strip()

    def _split_items(text: str):
        s = str(text or "").strip()
        if not s:
            return []
        parts = re.split(r"[\n,]+", s)
        return [p.strip() for p in parts if p and p.strip()]

    tags_list = _split_items(req.tags)
    rules_list = _split_items(req.rules)
    rewards_list = _split_items(req.rewards)

    conn = _db_connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO competitions (teacher_id, name, desc, type, mode, status, difficulty, participants, duration, register_time, competition_time, tags, detail_desc, rules, rewards) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)",
        (
            str(user["id"]),
            name,
            desc,
            ctype,
            mode,
            status,
            difficulty,
            duration,
            register_time,
            competition_time,
            json.dumps(tags_list, ensure_ascii=False),
            detail_desc,
            json.dumps(rules_list, ensure_ascii=False),
            json.dumps(rewards_list, ensure_ascii=False),
        ),
    )
    new_id = int(cur.lastrowid or 0)

    raw_items = getattr(req, "problems", None)
    items = raw_items if isinstance(raw_items, list) else []
    if mode == "problem_set" and items:
        task_ids = []
        norm = []
        seen = set()
        for idx, it in enumerate(items):
            if isinstance(it, PublishCompetitionProblemItem):
                task_id = str(it.task_id or "").strip()
                category = str(it.category or "").strip()
                points = int(it.points or 0)
                sort = int(it.sort or idx)
            elif isinstance(it, dict):
                task_id = str(it.get("task_id") or it.get("taskId") or "").strip()
                category = str(it.get("category") or "").strip()
                try:
                    points = int(it.get("points") or 0)
                except Exception:
                    points = 0
                try:
                    sort = int(it.get("sort") or idx)
                except Exception:
                    sort = idx
            else:
                continue

            if not task_id or task_id in seen:
                continue
            seen.add(task_id)
            if points <= 0:
                points = 100
            if points > 10000:
                points = 10000
            if len(category) > 30:
                category = category[:30]
            task_ids.append(task_id)
            norm.append((task_id, category, points, sort))

        if task_ids:
            placeholders = ",".join(["?"] * len(task_ids))
            cur.execute(
                f"SELECT id FROM checkin_tasks WHERE teacher_id = ? AND id IN ({placeholders})",
                (str(user["id"]),) + tuple(task_ids),
            )
            allowed = {str(r[0]) for r in (cur.fetchall() or [])}
            missing = [tid for tid in task_ids if tid not in allowed]
            if missing:
                conn.rollback()
                conn.close()
                raise HTTPException(status_code=400, detail="题目不存在或无权限添加")
            for (task_id, category, points, sort) in norm:
                cur.execute(
                    "INSERT OR REPLACE INTO competition_problems (competition_id, task_id, category, points, sort) VALUES (?, ?, ?, ?, ?)",
                    (new_id, task_id, category, points, sort),
                )
    conn.commit()
    conn.close()
    return {"success": True, "id": new_id}

@app.get("/api/teacher/competitions")
async def get_teacher_competitions(status: str = None, search: str = None, authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_teacher(user)
    tid = str(user["id"])
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    query = (
        "SELECT c.*, "
        "(SELECT COUNT(*) FROM competition_problems p WHERE p.competition_id = c.id) AS problem_count "
        "FROM competitions c WHERE (c.teacher_id = ? OR c.teacher_id IS NULL OR c.teacher_id = '')"
    )
    params = [tid]
    if status and status != "all":
        query += " AND c.status = ?"
        params.append(status)
    if search:
        query += " AND (c.name LIKE ? OR c.desc LIKE ? OR c.tags LIKE ?)"
        sp = f"%{search}%"
        params.extend([sp, sp, sp])
    query += " ORDER BY c.created_at DESC"
    cur.execute(query, params)
    rows = cur.fetchall() or []
    conn.close()
    comps = []
    for row in rows:
        tags = []
        if row["tags"]:
            if str(row["tags"]).startswith("[") and str(row["tags"]).endswith("]"):
                try:
                    tags = json.loads(row["tags"])
                except Exception:
                    tags = str(row["tags"]).split(",")
            else:
                tags = str(row["tags"]).split(",")
        rules = []
        if row["rules"]:
            if str(row["rules"]).startswith("[") and str(row["rules"]).endswith("]"):
                try:
                    rules = json.loads(row["rules"])
                except Exception:
                    rules = str(row["rules"]).split(",")
            else:
                rules = str(row["rules"]).split(",")
        rewards = []
        if row["rewards"]:
            if str(row["rewards"]).startswith("[") and str(row["rewards"]).endswith("]"):
                try:
                    rewards = json.loads(row["rewards"])
                except Exception:
                    rewards = str(row["rewards"]).split(",")
            else:
                rewards = str(row["rewards"]).split(",")
        comps.append({
            "id": row["id"],
            "teacherId": row["teacher_id"] if "teacher_id" in row.keys() else "",
            "name": row["name"],
            "desc": row["desc"],
            "type": row["type"],
            "mode": row["mode"] if "mode" in row.keys() else "general",
            "status": row["status"],
            "difficulty": row["difficulty"],
            "participants": row["participants"],
            "duration": row["duration"],
            "registerTime": row["register_time"],
            "competitionTime": row["competition_time"],
            "tags": tags,
            "detailDesc": row["detail_desc"],
            "rules": rules,
            "rewards": rewards,
            "problemCount": int(row["problem_count"] or 0),
            **_competition_access_meta(str(row["register_time"] or ""), str(row["competition_time"] or ""))
        })
    return {"success": True, "data": comps}

def _require_competition_owner(cur, competition_id: int, teacher_id: str):
    cur.execute("SELECT teacher_id, status FROM competitions WHERE id = ? LIMIT 1", (int(competition_id or 0),))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="测试不存在")
    existed_tid = str(row[0] or "")
    if existed_tid.strip() == "":
        try:
            cur.execute(
                "UPDATE competitions SET teacher_id = ? WHERE id = ? AND (teacher_id IS NULL OR teacher_id = '')",
                (str(teacher_id or ""), int(competition_id or 0)),
            )
        except Exception:
            pass
        existed_tid = str(teacher_id or "")
    if existed_tid != str(teacher_id or ""):
        raise HTTPException(status_code=403, detail="无权限操作该测试")
    return {"teacher_id": str(row[0] or ""), "status": str(row[1] or "")}

@app.post("/api/teacher/competitions/{competition_id}/end")
async def end_competition_early(competition_id: int, authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_teacher(user)
    cid = int(competition_id or 0)
    if cid <= 0:
        raise HTTPException(status_code=400, detail="参数不合法")
    conn = _db_connect()
    cur = conn.cursor()
    _require_competition_owner(cur, cid, str(user["id"]))
    cur.execute("UPDATE competitions SET status = 'ended', ended_at = CURRENT_TIMESTAMP WHERE id = ?", (cid,))
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/api/teacher/competitions/{competition_id}/submissions")
async def get_competition_submissions_for_teacher(competition_id: int, authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_teacher(user)
    cid = int(competition_id or 0)
    if cid <= 0:
        raise HTTPException(status_code=400, detail="参数不合法")
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    _require_competition_owner(cur, cid, str(user["id"]))
    cur.execute(
        """
        SELECT
          r.user_id,
          r.user_name,
          p.task_id,
          t.title AS task_title,
          p.category,
          p.points,
          p.sort,
          s.code,
          s.output,
          s.error,
          s.passed,
          s.score,
          s.feedback,
          s.graded_by,
          s.graded_at,
          s.created_at AS submitted_at
        FROM competition_registrations r
        JOIN competition_problems p ON p.competition_id = r.competition_id
        JOIN checkin_tasks t ON t.id = p.task_id
        LEFT JOIN competition_submissions s
          ON s.competition_id = r.competition_id AND s.task_id = p.task_id AND s.user_id = r.user_id
        WHERE r.competition_id = ?
        ORDER BY r.registered_at ASC, p.sort ASC, t.created_at ASC
        """,
        (cid,)
    )
    rows = cur.fetchall() or []
    conn.close()
    out = []
    for r in rows:
        out.append({
            "userId": str(r["user_id"] or ""),
            "userName": str(r["user_name"] or ""),
            "taskId": str(r["task_id"] or ""),
            "taskTitle": str(r["task_title"] or ""),
            "category": str(r["category"] or ""),
            "points": int(r["points"] or 0),
            "code": str(r["code"] or ""),
            "output": str(r["output"] or ""),
            "error": str(r["error"] or ""),
            "passed": bool(int(r["passed"] or 0)) if r["passed"] is not None else False,
            "score": (int(r["score"]) if r["score"] is not None else None),
            "feedback": str(r["feedback"] or ""),
            "gradedBy": str(r["graded_by"] or ""),
            "gradedAt": str(r["graded_at"] or ""),
            "submittedAt": str(r["submitted_at"] or "")
        })
    return {"success": True, "submissions": out}

@app.post("/api/teacher/competitions/{competition_id}/grade")
async def grade_competition_submission(competition_id: int, req: CompetitionGradeRequest, authorization: str = Header(None)):
    user = _require_user(authorization)
    _require_teacher(user)
    cid = int(competition_id or 0)
    if cid <= 0:
        raise HTTPException(status_code=400, detail="参数不合法")
    task_id = str(req.task_id or "").strip()
    user_id = str(req.user_id or "").strip()
    if not task_id or not user_id:
        raise HTTPException(status_code=400, detail="缺少参数")
    score = int(req.score or 0)
    if score < 0:
        score = 0
    feedback = str(req.feedback or "")

    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    _require_competition_owner(cur, cid, str(user["id"]))

    cur.execute(
        "SELECT points FROM competition_problems WHERE competition_id = ? AND task_id = ? LIMIT 1",
        (cid, task_id)
    )
    p = cur.fetchone()
    if not p:
        conn.close()
        raise HTTPException(status_code=400, detail="题目不属于该测试")
    max_points = int(p["points"] or 0)
    if max_points <= 0:
        max_points = 0
    if score > max_points:
        score = max_points

    cur.execute(
        "SELECT id FROM competition_submissions WHERE competition_id = ? AND task_id = ? AND user_id = ? LIMIT 1",
        (cid, task_id, user_id)
    )
    exist = cur.fetchone()
    if not exist:
        conn.close()
        raise HTTPException(status_code=400, detail="该学生尚未提交，无法批改")

    cur.execute(
        """
        UPDATE competition_submissions
        SET score = ?, feedback = ?, graded_by = ?, graded_at = CURRENT_TIMESTAMP
        WHERE competition_id = ? AND task_id = ? AND user_id = ?
        """,
        (score, feedback, str(user["id"]), cid, task_id, user_id)
    )
    conn.commit()
    conn.close()
    return {"success": True, "score": score}

@app.post("/api/competitions/register")
async def register_competition(req: CompetitionRegisterRequest, authorization: str = Header(None)):
    """测试报名"""
    user = _require_user(authorization)
    _require_student(user)
    cid = int(getattr(req, "competition_id", 0) or 0)
    if cid <= 0:
        raise HTTPException(status_code=400, detail="参数不合法")
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, name, status, register_time, competition_time FROM competitions WHERE id = ? LIMIT 1", (cid,))
    comp = cur.fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=404, detail="测试不存在")
    if str(comp["status"] or "") == "ended":
        conn.close()
        raise HTTPException(status_code=403, detail="测试已结束，暂不可报名")

    meta = _competition_access_meta(str(comp["register_time"] or ""), str(comp["competition_time"] or ""))
    if meta.get("registerValid") and (not meta.get("canRegister")):
        reason = str(meta.get("registerReason") or "")
        conn.close()
        if reason == "not_started":
            raise HTTPException(status_code=403, detail="未到报名时间，暂不可报名")
        if reason == "ended":
            raise HTTPException(status_code=403, detail="报名时间已结束，暂不可报名")
        raise HTTPException(status_code=403, detail="暂不可报名")

    cur.execute(
        "SELECT id FROM competition_registrations WHERE competition_id = ? AND user_id = ? LIMIT 1",
        (cid, str(user["id"])),
    )
    existing = cur.fetchone()
    if existing:
        conn.close()
        return {"success": True, "registered": True, "created": False, "message": "已报名"}

    cur.execute(
        "INSERT INTO competition_registrations (competition_id, competition_name, user_id, user_name) VALUES (?, ?, ?, ?)",
        (cid, str(comp["name"] or ""), str(user["id"]), str(user.get("name") or user.get("username") or "")),
    )
    cur.execute("UPDATE competitions SET participants = participants + 1 WHERE id = ?", (cid,))
    conn.commit()
    conn.close()
    return {"success": True, "registered": True, "created": True, "message": "报名成功"}

# ====================== 测试/积分商城 请求模型 ======================
class ExchangeRequest(BaseModel):
    goods_id: int
    user_id: str

# ====================== 积分接口 ======================
def get_user_points(user_id: str) -> int:
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT COALESCE(SUM(change), 0) FROM points_logs WHERE user_id = ?",
        (user_id,)
    )
    total = int(cur.fetchone()[0] or 0)
    conn.close()
    return max(total, 0)

def _add_points(cur, user_id: str, change: int, type: str, reason: str = ""):
    cur.execute(
        "INSERT INTO points_logs (user_id, change, type, reason) VALUES (?, ?, ?, ?)",
        (user_id, change, type, reason)
    )

def add_points(user_id: str, change: int, type: str, reason: str = ""):
    conn = _db_connect()
    cur = conn.cursor()
    _add_points(cur, user_id, change, type, reason)
    conn.commit()
    conn.close()

@app.get("/api/points")
async def get_points(user_id: str = Query(None)):
    """获取用户积分"""
    if not user_id:
        return {"success": False, "message": "缺少user_id"}
    return {"success": True, "points": get_user_points(user_id)}

@app.get("/api/points/goods")
async def get_points_goods(category: str = Query("all")):
    """获取积分商品列表"""
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    query = "SELECT * FROM points_goods WHERE 1=1"
    params = []
    if category and category != "all":
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY id ASC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    goods = []
    for row in rows:
        goods.append({
            "id": row["id"],
            "name": row["name"],
            "desc": row["desc"],
            "image": row["image"],
            "points": row["points"],
            "stock": row["stock"],
            "category": row["category"]
        })
    return {"success": True, "goods": goods}

@app.post("/api/teacher/points/goods")
async def teacher_create_points_goods(
    authorization: str = Header(None),
    name: str = Form(...),
    desc: str = Form(""),
    points: int = Form(...),
    stock: int = Form(...),
    category: str = Form("stationery"),
    image: UploadFile = File(None),
):
    user = _require_user(authorization)
    _require_teacher(user)

    n = str(name or "").strip()
    d = str(desc or "").strip()
    cat = str(category or "stationery").strip() or "stationery"
    try:
        pts = int(points)
        stk = int(stock)
    except Exception:
        raise HTTPException(status_code=400, detail="积分/库存必须为整数")

    if len(n) < 1 or len(n) > 40:
        raise HTTPException(status_code=400, detail="商品名称长度需为 1-40 位")
    if len(d) > 200:
        raise HTTPException(status_code=400, detail="商品描述最多 200 字")
    if pts < 0 or pts > 200000:
        raise HTTPException(status_code=400, detail="积分需在 0-200000 之间")
    if stk < 0 or stk > 100000:
        raise HTTPException(status_code=400, detail="库存需在 0-100000 之间")
    if cat not in ("stationery", "digital", "books", "virtual"):
        raise HTTPException(status_code=400, detail="分类不合法")

    image_url = ""
    if image is not None:
        ctype = str(getattr(image, "content_type", "") or "").lower()
        if not ctype.startswith("image/"):
            raise HTTPException(status_code=400, detail="只支持图片文件")
        raw = await image.read()
        if raw is None:
            raw = b""
        if len(raw) > 3 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="图片过大（最大 3MB）")
        ext = "png"
        if ctype in ("image/jpeg", "image/jpg"):
            ext = "jpg"
        elif ctype == "image/png":
            ext = "png"
        elif ctype == "image/webp":
            ext = "webp"
        elif ctype == "image/gif":
            ext = "gif"
        else:
            fn = str(getattr(image, "filename", "") or "").lower()
            if fn.endswith(".jpg") or fn.endswith(".jpeg"):
                ext = "jpg"
            elif fn.endswith(".png"):
                ext = "png"
            elif fn.endswith(".webp"):
                ext = "webp"
            elif fn.endswith(".gif"):
                ext = "gif"

        folder = _UPLOAD_ROOT / "points-goods"
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        file_name = f"{secrets.token_hex(16)}.{ext}"
        file_path = folder / file_name
        try:
            file_path.write_bytes(raw)
        except Exception:
            raise HTTPException(status_code=500, detail="图片保存失败")
        image_url = f"/api/uploads/points-goods/{file_name}"

    conn = _db_connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO points_goods (name, desc, image, points, stock, category) VALUES (?, ?, ?, ?, ?, ?)",
        (n, d, image_url, pts, stk, cat)
    )
    gid = int(cur.lastrowid or 0)
    conn.commit()
    conn.close()
    return {
        "success": True,
        "goods": {"id": gid, "name": n, "desc": d, "image": image_url, "points": pts, "stock": stk, "category": cat}
    }

@app.get("/api/points/records")
async def get_exchange_records(user_id: str = Query(None)):
    """获取兑换记录"""
    if not user_id:
        return {"success": False, "message": "缺少user_id"}
    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM exchange_records WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    records = []
    for row in rows:
        records.append({
            "id": row["id"],
            "goodsName": row["goods_name"],
            "image": row["goods_image"],
            "points": row["points"],
            "time": row["created_at"],
            "status": row["status"]
        })
    return {"success": True, "records": records}

@app.post("/api/points/exchange")
async def exchange_goods(req: ExchangeRequest):
    """兑换商品"""
    try:
        conn = _db_connect()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT COALESCE(SUM(change), 0) FROM points_logs WHERE user_id = ?",
            (req.user_id,)
        )
        current_points = int(cur.fetchone()[0] or 0)
        if current_points < 0:
            current_points = 0
        
        # 2. 获取商品信息
        cur.execute("SELECT * FROM points_goods WHERE id = ?", (req.goods_id,))
        goods_row = cur.fetchone()
        if not goods_row:
            conn.close()
            return {"success": False, "message": "商品不存在"}
        
        # 3. 检查库存和积分
        if goods_row[5] <= 0:  # stock
            conn.close()
            return {"success": False, "message": "商品已售罄"}
        
        if current_points < goods_row[4]:  # points
            conn.close()
            return {"success": False, "message": "积分不足"}
        
        _add_points(cur, req.user_id, -goods_row[4], "exchange", f"兑换商品：{goods_row[1]}")
        
        # 5. 减库存
        cur.execute("UPDATE points_goods SET stock = stock - 1 WHERE id = ?", (req.goods_id,))
        
        # 6. 添加兑换记录
        cur.execute(
            "INSERT INTO exchange_records (user_id, goods_id, goods_name, goods_image, points, status) VALUES (?, ?, ?, ?, ?, ?)",
            (req.user_id, req.goods_id, goods_row[1], goods_row[3], goods_row[4], "pending")
        )
        
        conn.commit()
        conn.close()
        return {"success": True, "message": "兑换成功"}
    except Exception as e:
        return {"success": False, "message": f"兑换失败: {str(e)}"}

# ====================== 排行榜接口 ======================
@app.get("/api/leaderboard")
async def get_leaderboard(limit: int = Query(50)):
    lim = int(limit or 50)
    if lim <= 0:
        lim = 50
    if lim > 200:
        lim = 200

    conn = _db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
          u.id AS user_id,
          COALESCE(u.name, u.username, '') AS name,
          COALESCE(u.avatar, '') AS avatar,
          COALESCE(s.passed_unique, 0) AS passed_unique,
          COALESCE(s.success_runs, 0) AS success_runs,
          COALESCE(s.total_runs, 0) AS total_runs,
          COALESCE(p.points, 0) AS points
        FROM users u
        LEFT JOIN (
          SELECT
            student_id,
            COUNT(*) AS total_runs,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS success_runs,
            COUNT(DISTINCT CASE WHEN success = 1 THEN problem_id ELSE NULL END) AS passed_unique
          FROM code_submissions
          WHERE student_id IS NOT NULL AND student_id != '' AND student_id != 'guest'
          GROUP BY student_id
        ) s ON s.student_id = u.id
        LEFT JOIN (
          SELECT
            user_id,
            CASE WHEN COALESCE(SUM(change), 0) < 0 THEN 0 ELSE COALESCE(SUM(change), 0) END AS points
          FROM points_logs
          GROUP BY user_id
        ) p ON p.user_id = u.id
        WHERE u.role = 'student'
        ORDER BY passed_unique DESC, success_runs DESC, total_runs DESC, points DESC, u.created_at ASC
        LIMIT ?
        """,
        (lim,)
    )
    rows = cur.fetchall() or []
    conn.close()

    out = []
    rank = 1
    for r in rows:
        out.append({
            "rank": rank,
            "userId": str(r["user_id"] or ""),
            "name": str(r["name"] or ""),
            "avatar": str(r["avatar"] or ""),
            "passedUnique": int(r["passed_unique"] or 0),
            "successRuns": int(r["success_runs"] or 0),
            "totalRuns": int(r["total_runs"] or 0),
            "points": int(r["points"] or 0)
        })
        rank += 1
    return {"success": True, "leaderboard": out}

# ====================== 每日签到接口 ======================
@app.post("/api/daily-signin")
async def daily_signin(user_id: str = Query(None), user_name: str = Query("")):
    """每日签到，得积分"""
    if not user_id:
        return {"success": False, "message": "缺少user_id"}
    
    today = datetime.now().strftime("%Y-%m-%d")
    conn = _db_connect()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM daily_signin WHERE user_id = ? AND signin_date = ?", (user_id, today))
        existing = cur.fetchone()
        if existing:
            conn.close()
            return {"success": False, "message": "今天已经签到过了", "alreadySigned": True}
        
        cur.execute("SELECT consecutive_days FROM daily_signin WHERE user_id = ? ORDER BY signin_date DESC LIMIT 1", (user_id,))
        last_row = cur.fetchone()
        consecutive = 1
        if last_row:
            from datetime import timedelta
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            cur.execute("SELECT id FROM daily_signin WHERE user_id = ? AND signin_date = ?", (user_id, yesterday))
            if cur.fetchone():
                consecutive = int(last_row[0] or 0) + 1
        
        points = 10 + (min(consecutive - 1, 6)) * 5
        cur.execute(
            "INSERT INTO daily_signin (user_id, signin_date, consecutive_days) VALUES (?, ?, ?)",
            (user_id, today, consecutive)
        )
        _add_points(cur, user_id, points, "signin", f"每日签到（连续{consecutive}天）")
        
        conn.commit()
        conn.close()
        return {"success": True, "message": "签到成功", "points": points, "consecutiveDays": consecutive}
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        return {"success": False, "message": f"签到失败: {str(e)}"}

@app.get("/api/daily-signin/status")
async def get_signin_status(user_id: str = Query(None)):
    """获取签到状态"""
    if not user_id:
        return {"success": False, "message": "缺少user_id"}
    today = datetime.now().strftime("%Y-%m-%d")
    conn = _db_connect()
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM daily_signin WHERE user_id = ? AND signin_date = ?", (user_id, today))
    signed = cur.fetchone() is not None
    
    cur.execute("SELECT consecutive_days FROM daily_signin WHERE user_id = ? ORDER BY signin_date DESC LIMIT 1", (user_id,))
    last_row = cur.fetchone()
    consecutive = last_row[0] if last_row else 0
    
    conn.close()
    return {"success": True, "signed": signed, "consecutiveDays": consecutive, "today": today}

from admin_api import create_admin_router
app.include_router(create_analysis_router(_db_connect, _require_user, _classify_knowledge_point))
app.include_router(create_content_router(_db_connect, _require_user))
app.include_router(create_admin_router(_db_connect, _require_user, _create_user, _hash_password))

# ====================== 启动服务 ======================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3002)
