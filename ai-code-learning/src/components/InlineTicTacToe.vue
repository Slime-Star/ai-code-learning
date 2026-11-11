<template>
  <section class="inline-mini-game" aria-label="休息一下，井字棋">
      <div class="mini-copy">
        <span class="mini-caption">TAKE A LITTLE BREAK</span>
        <h3>下一步，轮到你。</h3>
        <p class="mini-status" aria-live="polite">{{ status }}</p>
        <small>你执 X，电脑执 O</small>
        <button class="mini-reset" @click="reset">重来一局 ↻</button>
      </div>
        <div class="mini-board" role="group" aria-label="井字棋棋盘">
          <button v-for="(cell,index) in board" :key="index" :class="cell.toLowerCase()"
            :aria-label="`第 ${Math.floor(index/3)+1} 行第 ${index%3+1} 列，${cell || '空格'}`" :disabled="!!cell || !!result || thinking" @click="play(index)"><Transition name="mini-piece"><span v-if="cell" :key="cell">{{ cell }}</span></Transition></button>
          <svg v-if="winningStroke" class="mini-win-line" viewBox="0 0 300 300" fill="none" aria-hidden="true"><line v-bind="winningStroke" :class="result.winner.toLowerCase()" pathLength="1" /></svg>
        </div>
  </section>
</template>

<script setup>
import {ref,computed,onBeforeUnmount} from 'vue'
import {gameResult,bestComputerMove} from '@/utils/ticTacToe'
const board=ref(Array(9).fill('')),thinking=ref(false)
const result=computed(()=>gameResult(board.value))
const winningStroke=computed(()=>{
  if(result.value?.line.length!==3)return null
  const [first,,last]=result.value.line
  const x1=(first%3)*100+50,y1=Math.floor(first/3)*100+50
  const x2=(last%3)*100+50,y2=Math.floor(last/3)*100+50
  const dx=Math.sign(x2-x1)*22,dy=Math.sign(y2-y1)*22
  return {x1:x1-dx,y1:y1-dy,x2:x2+dx,y2:y2+dy}
})
const status=computed(()=>result.value ? result.value.winner === 'draw' ? '平局，再试试？' : result.value.winner === 'X' ? '你赢了，漂亮！' : '电脑赢了，再来一局？' : thinking.value ? '电脑思考中…' : '轮到你，连成一线即可获胜')
let timer
function play(index){
  if(board.value[index] || result.value || thinking.value)return
  board.value[index]='X'
  if(result.value)return
  thinking.value=true
  timer=setTimeout(()=>{const index=bestComputerMove(board.value);if(index>=0)board.value[index]='O';thinking.value=false},350)
}
function reset(){clearTimeout(timer);thinking.value=false;board.value=Array(9).fill('')}
onBeforeUnmount(()=>clearTimeout(timer))
</script>

<style scoped>
.inline-mini-game { display: flex; align-items: center; gap: 24px; color: #9b85b7; }
.mini-copy { width: 160px; }
.mini-caption { font: 8px Consolas,monospace; letter-spacing: 1.4px; color: #b4a4c8; }
h3 { font-size: 15px; font-weight: 500; margin: 8px 0; color: #927bab; }
.mini-status { font-size: 10px; line-height: 1.8; min-height: 36px; color: #a38fb6; }
.mini-copy small { display: block; font-size: 9px; color: #b3a3c4; margin: 3px 0 7px; }
.mini-reset { border: 0; background: transparent; padding: 4px 0; color: #9e83b8; cursor: pointer; font: inherit; font-size: 10px; }
.mini-board { position: relative; width: 138px; flex-shrink: 0; display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); }
.mini-board button { display: grid; place-items: center; aspect-ratio: 1; border: 0; border-right: 1px solid #d5c8e4; border-bottom: 1px solid #d5c8e4; background: transparent; color: #a084bf; font: 29px Consolas,monospace; cursor: pointer; transition: background 180ms; }
.mini-board button:nth-child(3n) { border-right: 0; }.mini-board button:nth-child(n+7) { border-bottom: 0; }
.mini-board button.o { color: #87a9b1; }.mini-board button:not(:disabled):hover { background: #eae0f34d; }.mini-board button:disabled { cursor: default; }
.mini-win-line { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 2; overflow: visible; }
.mini-win-line line { stroke: #a084bf; stroke-width: 3; stroke-linecap: round; vector-effect: non-scaling-stroke; stroke-dasharray: 1; animation: mini-win-draw 380ms cubic-bezier(.2,.75,.25,1) both; }
.mini-win-line line.o { stroke: #87a9b1; }
@keyframes mini-win-draw { from { stroke-dashoffset: 1; opacity: .3; } to { stroke-dashoffset: 0; opacity: 1; } }
.mini-piece-enter-active { transition: opacity 200ms,transform 240ms cubic-bezier(.16,1,.3,1); }.mini-piece-enter-from { opacity: 0; transform: scale(.4); }
@media (max-width: 480px) { .inline-mini-game { gap: 16px; }.mini-copy { width: 126px; }.mini-board { width: 120px; }h3 { font-size: 13px; } }
</style>
