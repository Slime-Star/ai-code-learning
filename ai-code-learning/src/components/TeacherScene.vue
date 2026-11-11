<template>
  <div class="teacher-scene" :class="`scene-${scene}`" aria-hidden="true">
    <div class="scene-orbit"><i></i><i></i></div>
    <template v-if="scene==='calendar'">
      <div class="scene-calendar"><span>DAILY PRACTICE</span><div><i v-for="n in 21" :key="n" :style="{'--i':n}" :class="{done:n<15}">{{ n<15?'✓':String(n).padStart(2,'0') }}</i></div></div>
    </template>
    <template v-else-if="scene==='data'">
      <div class="scene-bars"><i v-for="(height,index) in [35,58,46,78,64,92,83]" :key="index" :style="{'--height':height+'%','--i':index}"></i></div><span class="scene-code">skills.grow()</span>
    </template>
    <template v-else-if="scene==='draft'">
      <div class="scene-editor"><span>● ● ● &nbsp; lesson.js</span><code><i>01</i> const lesson = {<br><i>02</i> &nbsp; idea: 'create',<br><i>03</i> &nbsp; practice: true<br><i>04</i> };<b>▍</b></code></div>
    </template>
    <template v-else>
      <div class="scene-pipeline"><span>备课</span><i></i><span>练习</span><i></i><span>反馈</span></div><span class="scene-code">teach → practice → grow</span>
    </template>
  </div>
</template>
<script setup>
defineProps({scene:{type:String,default:'pipeline'}})
</script>
<style scoped>
.teacher-scene{position:relative;width:280px;height:160px;display:grid;place-items:center;isolation:isolate;pointer-events:none;color:#dfd3ff;flex-shrink:0}.scene-orbit{position:absolute;inset:8px 22px;border:1px solid #d7c4ff24;border-radius:50%;transform:rotate(-17deg);z-index:-1}.scene-orbit i{position:absolute;width:7px;height:7px;border-radius:50%;background:#bceae0;box-shadow:0 0 15px #bceae0;offset-path:ellipse(50% 50% at 50% 50%);animation:teacher-orbit 14s linear infinite}.scene-orbit i+i{animation-delay:-7s;background:#c4b2ff}.scene-pipeline{display:flex;align-items:center;gap:8px;animation:teacher-float 6s ease-in-out infinite}.scene-pipeline span{padding:16px 11px;background:#ffffff0d;border:1px solid #d5c3ff55;border-radius:12px;font-size:13px}.scene-pipeline>i{width:23px;height:1px;background:#d5c3ff55;position:relative}.scene-pipeline>i:after{content:'';position:absolute;width:5px;height:5px;background:#c2efdf;border-radius:50%;top:-2px;animation:teacher-packet 2.6s ease-in-out infinite}.scene-code{position:absolute;bottom:18px;font:11px Consolas,monospace;letter-spacing:1px;color:#d3c6ef99}.scene-calendar{width:185px;padding:10px 13px;background:#ffffff09;border:1px solid #cfc0f555;border-radius:13px;transform:rotate(-6deg);animation:teacher-float 7s ease-in-out infinite}.scene-calendar>span{font:9px Consolas,monospace;letter-spacing:2px}.scene-calendar>div{display:grid;grid-template-columns:repeat(7,1fr);gap:5px;margin-top:10px}.scene-calendar i{font:10px Consolas,monospace;text-align:center;padding:4px 0;color:#d6c5f577}.scene-calendar .done{border-radius:4px;background:#b9e9d91c;color:#c2efdf;animation:teacher-check 5s calc(var(--i)*.15s) ease-in-out infinite}.scene-bars{height:100px;display:flex;align-items:flex-end;gap:10px;width:200px;border-bottom:1px solid #ddcfff33;transform:rotate(-5deg)}.scene-bars i{width:20px;height:var(--height);background:linear-gradient(#d6c0ff,#a7dec466);border-radius:5px 5px 0 0;transform-origin:bottom;animation:teacher-bars 4s calc(var(--i)*-.35s) ease-in-out infinite}.scene-editor{width:235px;border-radius:12px;border:1px solid #cfc0f544;background:#1c143aaa;overflow:hidden;transform:rotate(-4deg);animation:teacher-float 7s ease-in-out infinite}.scene-editor>span{display:block;font:9px Consolas,monospace;padding:9px 12px;background:#d9c7ff0c;color:#d7c5ef99}.scene-editor code{display:block;padding:10px;font:11px/1.8 Consolas,monospace;color:#c8e4db}.scene-editor code i{font-style:normal;color:#beabd677;margin-right:12px}.scene-editor b{animation:teacher-cursor 1.3s step-end infinite}
@keyframes teacher-float{50%{translate:0 -8px}}@keyframes teacher-orbit{to{offset-distance:100%}}@keyframes teacher-packet{0%{translate:0 0;opacity:0}30%{opacity:1}100%{translate:23px 0;opacity:0}}@keyframes teacher-check{50%{background:#b9e9d940;color:#e1fff5}}@keyframes teacher-bars{50%{scale:1 .78}}@keyframes teacher-cursor{50%{opacity:0}}
@media(max-width:700px){.teacher-scene{width:220px;transform:scale(.85);height:135px}}
</style>
