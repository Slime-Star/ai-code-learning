<template>
  <div ref="scene" class="programming-workbench" role="img" aria-label="代码编写、处理与终端输出的立体流程示意" @pointermove="move" @pointerleave="reset">
    <div class="bench-space">
      <div class="bench-platform"><span></span><span></span><span></span></div>
      <svg class="bench-connections" viewBox="0 0 460 280" fill="none" aria-hidden="true">
        <path d="M115 137v51q0 12 12 12h77q14 0 14-14v-31m26-6v59q0 12 12 12h55q14 0 14-14v-17" />
        <path class="bench-signal" d="M115 137v51q0 12 12 12h77q14 0 14-14v-31m26-6v59q0 12 12 12h55q14 0 14-14v-17" />
        <circle r="3" fill="#e1d4ff"><animateMotion path="M115 137v51q0 12 12 12h77q14 0 14-14v-31" dur="4s" repeatCount="indefinite" /></circle>
      </svg>
      <div class="bench-pane bench-editor" aria-hidden="true">
        <div class="bench-toolbar"><i></i><i></i><i></i><span>hello.js</span></div>
        <div class="bench-code"><span class="line-no">01</span><span><b>const</b> message =</span><span class="line-no">02</span><span class="bench-string">'Hello, world!';</span><span class="line-no">03</span><span>console.<em>log</em>(message);</span></div>
        <div class="bench-code-lines"><i></i><i></i><i></i></div>
      </div>
      <div class="bench-processor" aria-hidden="true"><i class="chip-layer layer-bottom"></i><i class="chip-layer layer-middle"></i><i class="chip-layer layer-top"><span>&lt;/&gt;</span></i><span class="chip-caption">RUN</span></div>
      <div class="bench-pane bench-terminal" aria-hidden="true"><div class="bench-toolbar"><span>terminal</span><i class="terminal-light"></i></div><div class="terminal-command">&gt; node hello.js</div><div class="terminal-answer"><span>✓</span> Hello, world!<i></i></div><div class="terminal-rule"></div></div>
      <span class="bench-float-token token-function" aria-hidden="true">function()</span><span class="bench-float-token token-braces" aria-hidden="true">{ }</span>
    </div>
    <div class="bench-caption" aria-hidden="true"><span><i>01</i> 写代码</span><b>→</b><span><i>02</i> 理解运行</span><b>→</b><span><i>03</i> 看结果</span></div>
  </div>
</template>
<script setup>
import {ref,onBeforeUnmount} from 'vue'
import {usePersistentMotion} from '@/composables/usePersistentMotion'
const scene=ref(null)
let frame=0
usePersistentMotion(scene,()=> 'learning:programming-workbench')
function move(event){
  if(event.pointerType!=='mouse'||frame)return
  const bounds=scene.value.getBoundingClientRect()
  if(!bounds.width || !bounds.height)return
  const x=Math.max(-.5,Math.min(.5,(event.clientX-bounds.left)/bounds.width-.5))
  const y=Math.max(-.5,Math.min(.5,(event.clientY-bounds.top)/bounds.height-.5))
  frame=requestAnimationFrame(()=>{frame=0;scene.value?.style.setProperty('--bench-x',`${-9-y*6}deg`);scene.value?.style.setProperty('--bench-y',`${-12+x*10}deg`)})
}
function reset(){cancelAnimationFrame(frame);frame=0;scene.value?.style.removeProperty('--bench-x');scene.value?.style.removeProperty('--bench-y')}
onBeforeUnmount(()=>cancelAnimationFrame(frame))
</script>
<style scoped>
.programming-workbench{width:100%;max-width:470px;min-width:0;position:relative;perspective:1100px;user-select:none;color:#efe7ff;isolation:isolate}
.bench-space{height:270px;position:relative;transform:rotateX(var(--bench-x,-9deg)) rotateY(var(--bench-y,-12deg));transform-style:preserve-3d;transition:transform 380ms cubic-bezier(.2,.75,.25,1)}
.bench-platform{position:absolute;left:24px;right:14px;top:150px;height:120px;transform:rotateX(63deg) rotateZ(-8deg);border:1px solid #e9dcff55;border-radius:18px;background:linear-gradient(135deg,#ddd2ff22,#e7dcff09);box-shadow:0 8px 0 #d0b7f014,0 10px 0 #ddcaff22,0 30px 42px #30225735}
.bench-platform span{position:absolute;inset:14px;border:1px solid #e8d8ff18;border-radius:10px}.bench-platform span:nth-child(2){inset:30px}.bench-platform span:nth-child(3){inset:46px}
.bench-connections{position:absolute;inset:0;width:100%;height:100%;overflow:visible;stroke:#e0ceff66;stroke-width:1.6}.bench-signal{stroke:#eee6ff;stroke-dasharray:9 90;animation:bench-signal 7s linear infinite}
.bench-pane{position:absolute;overflow:hidden;background:linear-gradient(135deg,#fcfafff5,#eae1fff2);border:1px solid #ffffffb0;border-radius:12px;color:#665287;box-shadow:0 13px 28px #30224c35,4px 5px 0 #c7b4ee55;transform-style:preserve-3d}
.bench-editor{left:8px;top:29px;width:213px;height:151px;transform:translateZ(32px) rotateZ(-7deg);animation:bench-editor-float 8s ease-in-out infinite alternate}
.bench-toolbar{height:28px;display:flex;align-items:center;gap:5px;padding:0 10px;border-bottom:1px solid #b9a1d72b;background:#ffffff65}.bench-toolbar i{width:5px;height:5px;border-radius:50%;background:#bca4d9}.bench-toolbar i:nth-child(2){background:#b7c6de}.bench-toolbar i:nth-child(3){background:#a9c8be}.bench-toolbar span{margin-left:auto;font:9px Consolas,monospace;color:#8e7aa8}
.bench-code{display:grid;grid-template-columns:14px 1fr;gap:7px 7px;margin:15px 11px;font:10px/1.4 Consolas,monospace;white-space:nowrap}.line-no{color:#b5a5c8;font-size:8px}.bench-code b{color:#9973bc;font-weight:500}.bench-code em{font-style:normal;color:#668eb1}.bench-string{color:#6d9d96}
.bench-code-lines{display:flex;gap:7px;padding-left:32px}.bench-code-lines i{width:32px;height:3px;border-radius:3px;background:#b9a3d5;transform-origin:left;animation:bench-writing 8s ease-in-out infinite}.bench-code-lines i:nth-child(2){width:52px;opacity:.5;animation-delay:.5s}.bench-code-lines i:nth-child(3){width:22px;opacity:.3;animation-delay:1s}
.bench-processor{position:absolute;left:46%;top:112px;width:72px;height:88px;transform:translateZ(40px)}.chip-layer{position:absolute;width:65px;height:65px;border-radius:14px;transform:rotateX(42deg) rotateZ(-34deg);border:1px solid #efe1ff88;background:#a78bce99;box-shadow:0 6px 0 #6f4a9e55}.layer-bottom{top:24px;opacity:.5}.layer-middle{top:12px;opacity:.7}.layer-top{top:0;background:linear-gradient(135deg,#e1caff,#a487d2);display:grid;place-items:center;animation:bench-chip 5s ease-in-out infinite alternate}.layer-top span{font:24px Consolas,monospace;color:#6d4c99;transform:rotateZ(34deg)}.chip-caption{position:absolute;top:87px;left:17px;font:8px Consolas,monospace;letter-spacing:3px;color:#ded0f7}
.bench-terminal{right:0;top:125px;width:174px;height:107px;transform:translateZ(58px) rotateZ(5deg);animation:bench-terminal-float 7s ease-in-out infinite alternate}.bench-terminal .bench-toolbar span{margin:0}.bench-toolbar .terminal-light{margin-left:auto;background:#8bbab0;box-shadow:0 0 7px #8bbab055}.terminal-command{margin:12px 11px 8px;font:9px Consolas,monospace;color:#9984b0}.terminal-answer{margin:0 11px;font:10px Consolas,monospace;color:#6e948f;white-space:nowrap}.terminal-answer>span{margin-right:4px}.terminal-answer>i{display:inline-block;width:5px;height:10px;margin-left:4px;vertical-align:middle;background:#a08abb;animation:bench-cursor 1.5s step-end infinite}.terminal-rule{margin:11px;width:55%;height:2px;background:#cbb9de55}
.bench-float-token{position:absolute;font:10px Consolas,monospace;color:#e7daff88;animation:bench-token 6s ease-in-out infinite alternate}.token-function{right:22px;top:43px;transform:rotate(8deg)}.token-braces{left:34px;bottom:22px;font-size:22px;animation-delay:-2s}
.bench-caption{display:flex;align-items:center;justify-content:center;gap:12px;margin-top:4px;font-size:10px;color:#eee5ffb8}.bench-caption span{white-space:nowrap}.bench-caption i{font:8px Consolas,monospace;margin-right:5px;color:#e6d3ff75}.bench-caption b{font-weight:400;color:#e5d2ff66}
@keyframes bench-editor-float{to{transform:translate3d(0,-10px,42px) rotateZ(-4deg)}}@keyframes bench-terminal-float{to{transform:translate3d(0,-8px,65px) rotateZ(3deg)}}@keyframes bench-chip{to{translate:0 -7px;box-shadow:0 9px 0 #6f4a9e55}}@keyframes bench-signal{to{stroke-dashoffset:-198}}@keyframes bench-writing{0%,100%{transform:scaleX(.45);opacity:.4}40%,75%{transform:scaleX(1);opacity:.8}}@keyframes bench-cursor{50%{opacity:0}}@keyframes bench-token{to{translate:5px -8px;opacity:.4}}
@media(max-width:640px){.programming-workbench{max-width:390px;margin:0 auto}.bench-space{height:242px;transform:rotateX(-6deg) rotateY(-8deg)}.bench-editor{width:185px;height:145px;left:3px}.bench-code{font-size:9px;gap:7px 4px;margin-left:8px}.bench-terminal{width:152px;top:120px;right:1px}.terminal-answer{font-size:9px}.bench-platform{top:130px;height:110px}.bench-processor{left:45%;top:100px;scale:.85}.token-function{right:10px}.bench-caption{font-size:9px;gap:8px}}
</style>
