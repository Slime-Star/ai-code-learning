<template>
  <section class="study-toolkit" :class="{ 'on-purple': onPurple }" aria-label="编程学习小工具">
    <div class="toolkit-heading"><span aria-hidden="true">&lt;/&gt;</span><div><h2>让每一次练习，都有收获</h2><p>遇到卡点时，试试这三个小步骤</p></div></div>
    <div class="toolkit-items">
      <details v-for="item in items" :key="item.number">
        <summary><span class="step-number">{{ item.number }}</span><span>{{ item.title }}</span><span class="expand-mark" aria-hidden="true">+</span></summary>
        <div class="step-content"><p>{{ item.tip }}</p><router-link :to="item.to">{{ item.action }} <span aria-hidden="true">→</span></router-link></div>
      </details>
    </div>
  </section>
</template>

<script setup>
defineProps({ onPurple: Boolean })
const items = [
  { number: '01', title: '先理解，再动手', tip: '把一个知识点拆成输入、处理和输出，带着问题看课程，再用自己的话复述一次。', to: '/learning-center', action: '找一门课程' },
  { number: '02', title: '把想法写成代码', tip: '先写一个最小示例，观察运行结果。遇到错误时，从第一条报错开始，逐步验证。', to: '/', action: '去编程工作区' },
  { number: '03', title: '遇到问题，查一查', tip: '整理关键词，对照文档核对语法和用法。记录这次解决问题的思路，下次更容易想起来。', to: '/library', action: '打开资源库' }
]
</script>

<style scoped>
.study-toolkit { max-width: 1400px; margin: 0 auto; padding: 32px 20px 40px; color: #374151; }
.toolkit-heading { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.toolkit-heading > span { font: 700 24px Consolas, monospace; color: #8172cd; }
.toolkit-heading h2 { font-size: 18px; margin: 0 0 6px; }
.toolkit-heading p { font-size: 12px; color: #737c8c; margin: 0; }
.toolkit-items { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; align-items: start; }
details { border: 1px solid #e5e4f0; background: #fff; border-radius: 12px; overflow: hidden; transition: border-color 180ms, box-shadow 180ms; }
details[open] { border-color: #ad9ce2; box-shadow: 0 5px 16px #6b58af0c; }
summary { display: flex; align-items: center; gap: 10px; padding: 18px; cursor: pointer; list-style: none; font-size: 13px; font-weight: 600; }
summary::-webkit-details-marker { display: none; }
summary:focus-visible { outline: 3px solid #a5b4fc; outline-offset: -3px; }
.step-number { font: 12px Consolas, monospace; color: #8674bc; }
.expand-mark { margin-left: auto; color: #8674bc; font-size: 20px; transition: transform 180ms; }
details[open] .expand-mark { transform: rotate(45deg); }
.step-content { padding: 0 18px 18px; font-size: 12px; line-height: 1.9; }
.step-content p { margin: 0 0 10px; color: #6b7280; }
.step-content a { color: #7260b7; text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }
.step-content a:hover { text-decoration: underline; }
.on-purple { color: #fff; }
.on-purple .toolkit-heading > span, .on-purple .toolkit-heading p { color: #edeaff; }
.on-purple details { border-color: #ffffff38; background: #ffffff12; color: #fff; }
.on-purple details[open] { background: #ffffff20; border-color: #ffffff70; }
.on-purple .step-number, .on-purple .expand-mark, .on-purple .step-content p, .on-purple .step-content a { color: #f0edff; }
@media (max-width: 768px) { .toolkit-items { grid-template-columns: minmax(0,1fr); } }
</style>
