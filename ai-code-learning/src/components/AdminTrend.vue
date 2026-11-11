<template>
  <section class="admin-card admin-trend">
    <div class="card-title"><div><span class="admin-kicker">ACTIVITY</span><h2>平台运行趋势</h2></div><el-select :model-value="days" size="small" aria-label="趋势时间范围" :disabled="loading" @update:model-value="$emit('update:days',$event)"><el-option v-for="n in [7,14,30]" :key="n" :value="n" :label="`最近 ${n} 天`" /></el-select></div>
    <div class="trend-summary"><span>本期运行 <b>{{ total.toLocaleString('zh-CN') }}</b></span><span>每日平均 <b>{{ (total/Math.max(1,trend.length)).toFixed(1) }}</b></span><span>本期成功率 <b>{{ total?(successful/total*100).toFixed(1)+'%':'—' }}</b></span></div>
    <div class="trend-stage" @mouseleave="hovered=-1">
      <div v-if="selected" class="trend-tooltip"><strong>{{ selected.day }}</strong><span>运行 {{ selected.total }} 次 · 成功 {{ selected.successful }} 次</span><small>点击节点查看当天记录</small></div>
      <svg :key="trend.map(item=>item.day).join(',')" viewBox="0 0 720 215" preserveAspectRatio="none" aria-label="每日全部运行与成功运行趋势" role="img">
        <defs><linearGradient id="admin-trend-area" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#ad8ed1" stop-opacity=".28"/><stop offset="1" stop-color="#ad8ed1" stop-opacity="0"/></linearGradient></defs>
        <g class="trend-grid"><path v-for="y in [20,65,110,155,200]" :key="y" :d="`M16 ${y}H704`" /></g>
        <path class="trend-area" :d="`${totalPath} L${points.at(-1)?.x || 16} 200 L16 200 Z`" fill="url(#admin-trend-area)" />
        <path class="trend-line total-line" :d="totalPath" pathLength="1" /><path class="trend-line success-line" :d="successPath" pathLength="1" />
        <g v-for="(point,index) in points" :key="point.day" class="trend-target" role="button" tabindex="0" :aria-label="`${point.day}，运行${point.total}次，查看当天记录`" @mouseenter="hovered=index" @focus="hovered=index" @blur="hovered=-1" @click="$emit('day',point.day)" @keydown.enter.prevent="$emit('day',point.day)" @keydown.space.prevent="$emit('day',point.day)"><circle :cx="point.x" :cy="point.y" r="13" fill="transparent"/><circle class="trend-dot" :class="{active:hovered===index}" :cx="point.x" :cy="point.y" r="3.5" /></g>
      </svg>
      <span v-if="!total" class="trend-zero">本期暂无运行记录</span>
    </div>
    <div class="trend-axis"><span v-for="item in ticks" :key="item.day">{{ item.day.slice(5) }}</span></div>
    <div class="chart-legend"><span><i/>全部运行</span><span><i class="mint"/>成功运行</span><small>北京时间 · 点击节点可查看记录</small></div>
  </section>
</template>
<script setup>
import {computed,ref,watch} from 'vue'
const props=defineProps({trend:{type:Array,default:()=>[]},days:Number,loading:Boolean})
defineEmits(['update:days','day'])
const hovered=ref(-1),max=computed(()=>Math.max(1,...props.trend.map(item=>item.total)))
const total=computed(()=>props.trend.reduce((sum,item)=>sum+item.total,0)),successful=computed(()=>props.trend.reduce((sum,item)=>sum+item.successful,0))
const points=computed(()=>props.trend.map((item,index)=>({...item,x:16+index/Math.max(1,props.trend.length-1)*688,y:200-item.total/max.value*180,sy:200-item.successful/max.value*180})))
function curve(field){const list=points.value;if(!list.length)return 'M16 200';return list.reduce((path,item,index)=>{if(!index)return `M${item.x} ${item[field]}`;const previous=list[index-1],middle=(previous.x+item.x)/2;return `${path} C${middle} ${previous[field]},${middle} ${item[field]},${item.x} ${item[field]}`},'')}
const totalPath=computed(()=>curve('y')),successPath=computed(()=>curve('sy')),selected=computed(()=>props.trend[hovered.value])
const ticks=computed(()=>props.trend.filter((item,index)=>index%Math.max(1,Math.ceil((props.trend.length-1)/6))===0 || index===props.trend.length-1))
watch(()=>props.trend,()=>hovered.value=-1)
</script>
<style scoped>
.admin-trend .el-select{width:118px}.trend-summary{display:flex;gap:18px;flex-wrap:wrap;font-size:11px;color:#a08cae;margin:19px 0}.trend-summary b{color:#715783;font-weight:600;padding-left:5px}.trend-stage{position:relative;height:215px}.trend-stage svg{width:100%;height:100%;overflow:visible}.trend-grid path{stroke:#eee8f4;stroke-dasharray:3 6;fill:none}.trend-line{fill:none;stroke-width:2.5;vector-effect:non-scaling-stroke;stroke-linecap:round;stroke-dasharray:1;animation:admin-line-draw 950ms cubic-bezier(.2,.7,.2,1) both}.total-line{stroke:#ae8ccd}.success-line{stroke:#7aafa0;animation-delay:80ms}.trend-area{animation:admin-area-in 900ms ease both}.trend-dot{fill:#fff;stroke:#a786c7;stroke-width:2;transition:r .2s,fill .2s}.trend-dot.active,.trend-target:focus .trend-dot{r:5;fill:#b196ce}.trend-target{cursor:pointer;outline:none}.trend-tooltip{position:absolute;z-index:2;top:0;left:50%;translate:-50% 0;display:grid;gap:5px;pointer-events:none;padding:11px 15px;background:#34273fee;color:#f3e9fc;border-radius:10px;font-size:10px;box-shadow:0 6px 20px #3824411a;white-space:nowrap}.trend-tooltip strong{font-size:11px}.trend-tooltip small{font-size:9px;color:#c8b8d8}.trend-axis{display:flex;justify-content:space-between;font:9px Consolas,monospace;color:#aa98b6;margin:12px 0 18px}.chart-legend{display:flex;gap:15px;align-items:center;flex-wrap:wrap;font-size:10px;color:#9e8aac}.chart-legend i{display:inline-block;width:7px;height:7px;border-radius:50%;background:#ae8ccd;margin-right:5px}.chart-legend .mint{background:#7aafa0}.chart-legend small{margin-left:auto;font-size:9px;color:#b7a5c1}.trend-zero{position:absolute;left:50%;top:45%;translate:-50% -50%;font-size:12px;color:#ae9ab9}@keyframes admin-line-draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}@keyframes admin-area-in{from{opacity:0}to{opacity:1}}
</style>
