<template>
  <div class="whitespace-game" :class="{inverse,compact}">
    <div class="art-space"><CodeLandscape :variant="scene === 'books' ? 'terminal' : scene === 'team' ? 'chip' : 'planet'" :inverse="inverse" /><AnimatedCompanion v-if="scene === 'team'" class="game-companion" kind="plane" /><span class="tiny-code" aria-hidden="true">{{ decorativeCode }}</span></div>
    <section class="micro-game" :class="{completed: colorSolved && game === 'color' || matched.size === 8 && game === 'memory' || lightsSolved && game === 'lights' || puzzleDone && game === 'puzzle'}" :aria-label="title">
      <div class="micro-copy"><span class="micro-label">{{ label }}</span><h3>{{ title }}</h3><p aria-live="polite">{{ status }}</p><button class="micro-reset" @click="reset">{{ game === 'color' ? '换一组颜色' : '重来一局' }} ↻</button></div>
      <div v-if="game === 'color'" class="color-board"><code>{{ target }}</code><div><button v-for="color in choices" :key="color" :style="{backgroundColor:color}" :aria-label="`颜色 ${color}`" :disabled="colorSolved" @click="chooseColor(color)"><span v-if="colorSolved && color === target">✓</span></button></div></div>
      <div v-else-if="game === 'memory'" class="micro-board memory-board" role="group" aria-label="符号配对棋盘"><button v-for="(card,index) in cards" :key="index" :class="{flipped: flipped.includes(index),matched: matched.has(index)}" :disabled="matched.has(index) || flipped.includes(index) || locked" :aria-label="`第 ${index+1} 张卡片，${flipped.includes(index) || matched.has(index) ? card : '未翻开'}`" @click="flip(index)">{{ flipped.includes(index) || matched.has(index) ? card : '·' }}</button></div>
      <div v-else-if="game === 'lights'" class="micro-board square-board lights-board" role="group" aria-label="点灯棋盘"><button v-for="(lit,index) in lights" :key="index" :class="{lit}" :aria-pressed="lit" :aria-label="`第 ${index+1} 盏灯`" :disabled="lightsSolved" @click="pressLight(index)"><span></span></button></div>
      <TransitionGroup v-else name="puzzle-slide" tag="div" class="micro-board square-board puzzle-board" role="group" aria-label="数字滑块拼图"><button v-for="(tile,index) in puzzle" :key="tile" :class="{empty:!tile}" :aria-label="tile ? `移动数字 ${tile}` : '空格'" :disabled="!tile || puzzleDone || !gridNeighbors(puzzle.indexOf(0)).includes(index)" @click="slide(index)">{{ tile || '' }}</button></TransitionGroup>
    </section>
  </div>
</template>

<script setup>
import {computed,ref,watch,onBeforeUnmount} from 'vue'
import CodeLandscape from '@/components/CodeLandscape.vue'
import AnimatedCompanion from '@/components/AnimatedCompanion.vue'
import {shuffled,gridNeighbors,toggleLights,newLights,slideTile,puzzleSolved,newPuzzle} from '@/utils/miniGames'
const props=defineProps({game:{type:String,default:'color'},scene:{type:String,default:'books'},inverse:Boolean,compact:Boolean})
const title=computed(()=>({color:'找一抹颜色',memory:'符号碰个面',lights:'关掉九盏灯',puzzle:'把数字归位'}[props.game]))
const label=computed(()=>({color:'HEX / COLOR',memory:'PAIR / MATCH',lights:'BIT / TOGGLE',puzzle:'MOVE / SORT'}[props.game]))
const decorativeCode=computed(()=>({color:'color: #curiosity;',memory:'find(pair) → match;',lights:'light = !light;',puzzle:'swap(tile, empty);'}[props.game]))
const choices=ref([]),target=ref(''),colorSolved=ref(false),wrong=ref(false)
const cards=ref([]),flipped=ref([]),matched=ref(new Set()),locked=ref(false)
const lights=ref([]),puzzle=ref([]),moves=ref(0)
const lightsSolved=computed(()=>lights.value.length === 9 && lights.value.every(value=>!value))
const puzzleDone=computed(()=>puzzle.value.length === 9 && puzzleSolved(puzzle.value))
let timer
const status=computed(()=>{
  if(props.game==='color')return colorSolved.value?'✓ 找到了！':wrong.value?'再观察一下，试试其他色块':'点击与色值对应的色块'
  if(props.game==='memory')return matched.value.size===8?'✓ 全部配对成功！':`找到相同符号 · ${matched.value.size/2}/4 对`
  if(props.game==='lights')return lightsSolved.value?`✓ ${moves.value} 步完成！`:'点击一格，切换自己和相邻灯'
  return puzzleDone.value?`✓ ${moves.value} 步归位！`:'点击空格旁的数字，排成 1—8'
})
function reset(){
  clearTimeout(timer);moves.value=0
  if(props.game==='color'){
    const palette=['#B99AD8','#8FB7C9','#D9ABBD','#A5BFA0','#D7B989','#99A1D0']
    const next=shuffled(palette.filter(color=>color!==target.value))[0]
    choices.value=shuffled([next,...shuffled(palette.filter(color=>color!==next)).slice(0,2)]);target.value=next;colorSolved.value=false;wrong.value=false
  }else if(props.game==='memory'){cards.value=shuffled(['{}','[]','()','</>','{}','[]','()','</>']);flipped.value=[];matched.value=new Set();locked.value=false}
  else if(props.game==='lights')lights.value=newLights()
  else puzzle.value=newPuzzle()
}
function chooseColor(color){if(colorSolved.value)return;colorSolved.value=color===target.value;wrong.value=!colorSolved.value}
function flip(index){
  if(locked.value||matched.value.has(index)||flipped.value.includes(index))return
  flipped.value.push(index)
  if(flipped.value.length<2)return
  const [a,b]=flipped.value
  if(cards.value[a]===cards.value[b]){matched.value.add(a);matched.value.add(b);flipped.value=[]}
  else{locked.value=true;timer=setTimeout(()=>{flipped.value=[];locked.value=false},650)}
}
function pressLight(index){if(lightsSolved.value)return;lights.value=toggleLights(lights.value,index);moves.value++}
function slide(index){if(puzzleDone.value)return;const next=slideTile(puzzle.value,index);if(next!==puzzle.value){puzzle.value=next;moves.value++}}
watch(()=>props.game,reset,{immediate:true})
onBeforeUnmount(()=>clearTimeout(timer))
</script>

<style scoped>
.whitespace-game { max-width: 1280px; margin: 8px auto 0; width: calc(100% - 40px); display: grid; grid-template-columns: minmax(0,1fr) auto; gap: 28px; align-items: center; padding: 12px 20px; --ink: #937dac; --muted: #a995bc; --line: #ded2ea; --fill: #eee7f44d; --piece: #a68bbf; }
.art-space { position: relative; min-width: 0; }.tiny-code { position: absolute; bottom: 10px; right: 12%; font: 9px Consolas,monospace; color: #b3a0c7; opacity: .65; pointer-events: none; }
.micro-game { display: flex; align-items: center; gap: 20px; color: var(--ink); }.micro-copy { width: 148px; }.micro-label { color: var(--muted); font: 8px Consolas,monospace; letter-spacing: 1.4px; }h3 { margin: 8px 0; font-size: 14px; font-weight: 500; }p { font-size: 10px; color: var(--muted); line-height: 1.9; min-height: 38px; }.micro-reset { padding: 5px 0; border: 0; background: none; color: var(--ink); font: inherit; font-size: 10px; cursor: pointer; }
.micro-board { display: grid; gap: 5px; flex-shrink: 0; }.micro-board button { display: grid; place-items: center; border: 1px solid var(--line); background: transparent; color: var(--piece); border-radius: 5px; cursor: pointer; font: 18px Consolas,monospace; padding: 0; transition: background 180ms,transform 180ms; }.micro-board button:disabled { cursor: default; }.micro-board button:not(:disabled):hover { background: var(--fill); transform: translateY(-2px); }.memory-board { width: 140px; grid-template-columns: repeat(4,minmax(0,1fr)); }.memory-board button { aspect-ratio: 1; font-size: 12px; }.memory-board button.flipped { background: var(--fill); }.memory-board button.matched { opacity: .5; border-style: dashed; }.square-board { width: 120px; grid-template-columns: repeat(3,minmax(0,1fr)); }.square-board button { aspect-ratio: 1; }.lights-board button span { width: 9px; height: 9px; border: 1px solid var(--line); border-radius: 50%; transition: background 180ms,box-shadow 180ms; }.lights-board button.lit span { background: #c2a8df; border-color: #b49acb; box-shadow: 0 0 8px #b8a0d65c; }.puzzle-board .empty { border-color: transparent; }.color-board { width: 132px; flex-shrink: 0; }.color-board code { display: block; margin-bottom: 12px; text-align: center; font: 12px Consolas,monospace; color: var(--ink); }.color-board > div { display: flex; gap: 8px; }.color-board button { width: 38px; height: 38px; border: 1px solid #ffffff50; border-radius: 8px; cursor: pointer; color: #fff; font-size: 18px; transition: transform 180ms; }.color-board button:not(:disabled):hover { transform: translateY(-4px); }
.inverse { --ink: #f0e6ff; --muted: #d8c8ef; --line: #e6d7fc55; --fill: #ffffff10; --piece: #e6d7fb; }.inverse .tiny-code { color: #e6d7fb; }
@media (max-width: 850px) { .whitespace-game { grid-template-columns: minmax(0,1fr); justify-items: center; padding: 24px 0; }.art-space { display: none; } }
@media (max-width: 400px) { .micro-copy { width: 125px; }.micro-game { gap: 14px; }.memory-board { width: 128px; }.color-board { width: 120px; }.color-board button { width: 34px; height: 34px; } }
.whitespace-game.compact { width: 100%; padding: 0; margin: 0; display: block; }
.compact .art-space { display: none; }
.compact .micro-game { flex-direction: column; gap: 14px; }
.compact .micro-copy { width: 100%; }
.compact .micro-copy p { min-height: 0; }
.game-companion { position: absolute; right: -4px; bottom: 15px; width: 125px; }
@media (max-width: 1200px) { .game-companion { display: none; } }
.memory-board button.flipped { animation: memory-flip 300ms ease-out; }
.memory-board button.matched { animation: matched-glow 650ms ease-out; }
.lights-board button.lit span { animation: light-breathe 2.6s ease-in-out infinite alternate; }
.puzzle-board .puzzle-slide-move { transition: transform 220ms cubic-bezier(.2,.75,.25,1); }
.color-board button { animation: swatch-appear 350ms cubic-bezier(.16,1,.3,1) both; }.color-board button:nth-child(2) { animation-delay: 50ms; }.color-board button:nth-child(3) { animation-delay: 100ms; }
.micro-game.completed .micro-board, .micro-game.completed .color-board { animation: game-complete 600ms ease-out; }
@keyframes memory-flip { from { transform: perspective(220px) rotateY(75deg) scale(.9); } to { transform: perspective(220px) rotateY(0) scale(1); } }
@keyframes matched-glow { 40% { box-shadow: 0 0 12px #bea3db80; transform: scale(1.07); } }
@keyframes light-breathe { from { box-shadow: 0 0 3px #b8a0d640; transform: scale(.85); } to { box-shadow: 0 0 11px #b8a0d699; transform: scale(1.1); } }
@keyframes swatch-appear { from { opacity: 0; transform: translateY(6px) scale(.9); } to { opacity: 1; transform: translateY(0) scale(1); } }
@keyframes game-complete { 40% { filter: drop-shadow(0 0 6px #b69ad661); } }
@media (max-width: 900px) { .compact .micro-game { flex-direction: row; }.compact .micro-copy { width: 140px; } }
@media (max-width: 480px) { .compact .micro-game { gap: 10px; }.compact .micro-copy { width: auto; flex: 1; min-width: 0; } }
</style>
