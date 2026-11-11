<template>
  <div class="admin-shell" :class="{'sidebar-collapsed': collapsed}">
    <aside class="admin-sidebar">
      <div class="console-brand"><span class="brand-mark">◈</span><div class="brand-text">慧编云 · 管理中心<small>ADMIN WORKSPACE</small></div></div>
      <el-input v-if="!collapsed" v-model="moduleSearch" clearable class="module-search" placeholder="查找管理模块" aria-label="查找管理模块"><template #prefix><el-icon><Search/></el-icon></template></el-input>
      <nav aria-label="管理模块"><router-link to="/admin" class="side-link overview-link" :class="{selected: !moduleId}" title="数据总览"><el-icon><DataAnalysis/></el-icon><span>数据总览</span></router-link>
      <div v-for="group in groups" :key="group" class="module-group"><p v-if="!collapsed">{{ group }}</p>
        <router-link v-for="item in filteredModules.filter(m => m.group === group)" :key="item.id" :to="`/admin/${item.id}`" class="side-link" :class="{selected: moduleId === item.id}" :title="item.label"><el-icon><component :is="moduleIcon(item.id)"/></el-icon><span>{{ item.label }}</span></router-link>
      </div><p v-if="moduleSearch && !filteredModules.length" class="side-empty">没有匹配的管理模块</p></nav>
      <button class="sidebar-toggle" :aria-label="collapsed?'展开导航':'收起导航'" :aria-expanded="!collapsed" @click="collapsed=!collapsed"><el-icon><Expand v-if="collapsed"/><Fold v-else/></el-icon><span v-if="!collapsed">收起导航</span></button>
    </aside>
    <main class="admin-main" v-loading="initializing">
      <div class="admin-breadcrumb">管理工作台 <span>/</span> {{ currentModule?.group || '平台概览' }} <span class="admin-account">{{ currentUser?.name || '管理员' }}</span></div>
      <header class="admin-header"><div><span class="admin-kicker">{{ moduleId ? 'DATA MANAGEMENT' : 'WORKSPACE OVERVIEW' }}</span><h1>{{ currentModule?.label || '数据总览' }}</h1><p>{{ moduleDescription }}</p><span v-if="updatedAt" class="update-time">最近更新 {{ formatTime(updatedAt) }}</span></div><AdminPulse v-if="!moduleId"/><el-button class="admin-refresh" :disabled="loading || initializing" :aria-busy="loading || initializing" @click="requestRefresh"><el-icon class="admin-refresh-icon" :class="{'is-refreshing': loading || initializing}"><Refresh/></el-icon><span>刷新数据</span></el-button></header>
      <div class="mobile-module"><el-select :model-value="moduleId || 'overview'" aria-label="选择管理模块" @change="v => router.push(v !== 'overview' ? `/admin/${v}` : '/admin')"><el-option label="数据总览" value="overview"/><el-option v-for="m in modules" :key="m.id" :label="`${m.group} · ${m.label}`" :value="m.id"/></el-select></div>
      <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" class="page-error"><template #default><el-button v-if="needsLogin" link type="primary" @click="relogin">重新登录</el-button><el-button v-else link type="primary" @click="refresh">重试加载</el-button></template></el-alert>
      <div ref="contentElement" class="admin-content" :style="scrollFloor ? {minHeight: `${scrollFloor}px`} : undefined"><Transition name="admin-module" @before-leave="el => el.inert = true"><div :key="moduleId || 'overview'" class="admin-module-view"><template v-if="!moduleId && overview">
        <div class="overview-top"><div class="summary-banner"><span class="admin-kicker">CODE · LEARN · GROW</span><span>累计代码运行</span><strong><AnimatedNumber :value="overview.runs.total" animate/><small>次</small></strong><p>今日 {{ number(overview.runs.today) }} 次 · 累计 {{ number(overview.runs.activeUsers) }} 位用户参与运行</p><router-link to="/admin/runs">查看运行记录 <span>↗</span></router-link><span class="banner-code" aria-hidden="true">&lt;/&gt;</span></div><div class="success-stat admin-card"><div class="success-ring"><svg viewBox="0 0 110 110" aria-hidden="true"><circle cx="55" cy="55" r="47"/><circle cx="55" cy="55" r="47" :style="{'stroke-dasharray':`${Number(successRate)*2.9531} 295.31`}"/></svg><strong>{{ successRate }}<small>%</small></strong></div><div><h2>执行成功率</h2><p>累计运行结果</p><span class="outcome good">成功 {{ number(overview.runs.successful) }}</span><span class="outcome bad">失败 {{ number(overview.runs.failed) }}</span></div></div></div>
        <div class="metric-grid"><router-link v-for="(m,index) in metrics" :key="m.id" :to="`/admin/${m.id}`" class="metric-card" :style="{'--card-index':index}"><el-icon><component :is="moduleIcon(m.id)"/></el-icon><span>{{ m.label }}</span><strong><AnimatedNumber :value="m.value || 0" animate/></strong><span v-if="m.detail" class="metric-detail">{{ m.detail }}</span><small>查看数据 ↗</small></router-link></div>
        <div class="chart-grid"><AdminTrend :trend="overview.trend" v-model:days="days" :loading="loading" @update:days="refresh" @day="openDay"/>
        <section class="admin-card language-card"><div class="card-title"><div><span class="admin-kicker">LANGUAGES</span><h2>编程语言分布</h2></div><small>累计运行</small></div><el-empty v-if="!overview.languages.length" description="暂无运行数据" :image-size="70"/><template v-else><div class="language-donut" :style="{background:languageGradient}"><div><strong>{{ number(overview.runs.total) }}</strong><span>累计运行次数</span></div></div><button v-for="(l,index) in overview.languages" :key="l.name" class="language-row" :disabled="!languageLabels[l.name]" @click="openLanguage(l.name)"><i :style="{background:chartColors[index%chartColors.length]}"/><span>{{ languageLabels[l.name] || l.name }}</span><b>{{ number(l.value) }}</b><small>{{ (l.value/Math.max(1,overview.runs.total)*100).toFixed(1) }}%</small><span>↗</span></button><p class="card-caption">点击语言查看对应运行记录</p></template></section></div>
        <section class="admin-card"><div class="card-title"><h2>运行活跃用户</h2><router-link to="/admin/runs">查看全部运行记录 ↗</router-link></div><el-table :data="overview.active" stripe><el-table-column type="index" label="排名" width="70"/><el-table-column prop="name" label="用户"/><el-table-column prop="student_id" label="用户编号" min-width="180"/><el-table-column prop="runs" label="运行次数"><template #default="{row}"><el-button link type="primary" @click="router.push({path:'/admin/runs',query:{q:row.student_id}})">{{ number(row.runs) }} ↗</el-button></template></el-table-column><el-table-column prop="successful" label="成功次数"/></el-table></section>
        <section class="admin-card recent-audit"><div class="card-title"><div><span class="admin-kicker">ACTIVITY LOG</span><h2>最近管理操作</h2></div><router-link to="/admin/audit">全部记录 ↗</router-link></div><p v-if="auditError" class="card-caption">{{ auditError }}</p><el-empty v-else-if="!recentAudit.length" description="暂无管理操作" :image-size="55"/><button v-for="item in recentAudit" :key="item._key" class="audit-entry" @click="openDetail(item,'audit')"><span class="audit-dot"></span><b>{{ item.admin_name || '管理员' }}</b><span>{{ actionLabels[item.action] || item.action }} · {{ modules.find(m=>m.id===item.module)?.label || item.module }}</span><time>{{ formatTime(item.created_at) }}</time><span>查看变更 ↗</span></button></section>
        <p class="data-footnote">统计来自已保存的全站记录；删除运行记录会同步调整统计。更新时间：{{ formatTime(updatedAt) }}</p>
      </template>
      <template v-if="moduleId && currentModule">
        <el-alert v-if="currentModule.hint" :title="currentModule.hint" type="info" :closable="false" show-icon class="module-hint"/>
        <section class="admin-card data-card"><div class="data-toolbar"><el-input v-model="search" clearable :maxlength="200" placeholder="搜索名称、编号或内容" aria-label="搜索记录" @keyup.enter="searchRecords" @clear="searchRecords"/><el-button @click="searchRecords">搜索</el-button><span class="result-count">共 {{ number(total) }} 条</span><el-popover popper-class="admin-overlay admin-columns-popover" placement="bottom" width="220" trigger="click"><template #reference><el-button>显示列</el-button></template><el-checkbox-group v-model="visibleColumns" :min="1" class="admin-column-list"><el-checkbox v-for="f in availableFields" :key="f.name" :value="f.name">{{ f.label }}</el-checkbox></el-checkbox-group><el-button link type="primary" @click="resetColumns">恢复默认列</el-button></el-popover><div class="toolbar-actions"><el-button :loading="exporting" @click="exportCsv">导出 CSV</el-button><el-button v-if="currentModule.create" type="primary" :loading="preparing" @click="openEditor()">新建{{ currentModule.label === '积分流水' ? '积分调整' : '记录' }}</el-button></div></div>
        <div v-if="currentModule.filters?.length" class="data-filters"><label v-for="f in currentModule.filters" :key="f.name"><span>{{ f.label }}</span><el-date-picker v-if="f.type==='date'" v-model="filters[f.name]" type="date" value-format="YYYY-MM-DD" placeholder="全部日期" :aria-label="f.label" @change="searchRecords"/><el-select v-else v-model="filters[f.name]" clearable :placeholder="'全部'+f.label" :aria-label="f.label" @change="searchRecords"><el-option v-for="o in f.options" :key="o" :label="optionLabel(f.name,o)" :value="o"/></el-select></label><el-button v-if="appliedSearch || Object.keys(appliedFilters).length" link type="primary" @click="resetSearch">清除筛选</el-button></div>
        <p v-if="appliedSearch || Object.keys(appliedFilters).length" class="filter-summary">当前筛选：{{ appliedSearch ? '“'+appliedSearch+'” · ' : '' }}{{ filterDescription }}</p>
        <el-table :data="rows" v-loading="loading" stripe row-key="_key" :row-class-name="tableRowClass" max-height="680" style="width:100%" empty-text="暂无符合条件的数据"><el-table-column v-for="f in tableFields" :key="f.name" :prop="f.name" :label="f.label" :min-width="f.name === 'id' || f.name.endsWith('_id') ? 170 : 135" show-overflow-tooltip><template #default="{row}"><el-tag v-if="f.name === 'role'" size="small" :type="row.role === 'admin' ? 'danger' : row.role === 'teacher' ? 'warning' : 'info'">{{ roleLabels[row.role] || row.role }}</el-tag><el-tag v-else-if="['success','passed'].includes(f.name)" size="small" :type="Number(row[f.name]) ? 'success' : 'danger'">{{ optionLabel(f.name,row[f.name]) }}</el-tag><el-tag v-else-if="['status','pinned','action'].includes(f.name)" size="small" type="info">{{ optionLabel(f.name,row[f.name]) }}</el-tag><span v-else>{{ displayCell(row[f.name], f.name) }}</span></template></el-table-column><el-table-column label="操作" width="188" fixed="right"><template #default="{row}"><el-button link type="primary" @click="openDetail(row,moduleId)">详情</el-button><el-button v-if="canEdit" link type="primary" @click="openEditor(row)">编辑</el-button><el-button v-if="currentModule.delete" link type="danger" :loading="previewKey === row._key" @click="prepareDelete(row)">{{ moduleId === 'sessions' ? '注销' : '删除' }}</el-button></template></el-table-column></el-table>
        <div class="table-pagination"><el-pagination v-model:current-page="page" v-model:page-size="pageSize" :page-sizes="[10,20,50,100]" :total="total" layout="total, sizes, prev, pager, next" @current-change="loadRows" @size-change="changePageSize"/></div><p class="card-caption">导出将包含当前筛选下的全部记录。</p></section>
      </template></div></Transition></div>
    </main>
    <el-drawer v-model="detailOpen" title="记录详情" size="min(760px, 96vw)" class="admin-overlay admin-detail-drawer" append-to-body><div class="detail-heading"><span class="admin-kicker">RECORD DETAILS</span><h2>{{ detail?.name || detail?.title || detail?.username || detailModule?.label }}</h2><p>{{ detailModule?.label }} · 完整记录</p></div><section v-if="auditChanges.length" class="audit-diff"><h3>字段变更</h3><div v-for="item in auditChanges" :key="item.name" class="diff-field"><strong>{{ item.label }}</strong><div><section><small>修改前</small><pre>{{ item.before }}</pre></section><section><small>修改后</small><pre>{{ item.after }}</pre></section></div></div></section><dl class="detail-list"><template v-for="f in detailFields" :key="f.name"><dt>{{ f.label }}<el-button v-if="detail?.[f.name] != null" link type="primary" @click="copyValue(detail[f.name])">复制</el-button></dt><dd :class="{code:['code','output','error','starter_code','solution_code','starterCode','solutionCode'].includes(f.name)}">{{ displayCell(detail?.[f.name], f.name) }}</dd></template></dl></el-drawer>
    <el-dialog v-model="editorOpen" :title="`${editing ? '编辑' : '新建'} · ${currentModule?.label}`" width="min(760px, 95vw)" class="admin-overlay admin-editor-dialog" :close-on-click-modal="false" :before-close="closeEditor" append-to-body>
      <p class="editor-note">{{ editing ? '编辑完成后保存，变更会写入操作日志。' : '填写记录内容，关联信息可搜索选择。' }}<span v-if="formDirty"> · 尚未保存</span></p><el-alert v-if="formError" :title="formError" type="error" :closable="false" class="module-hint"/>
      <el-form label-position="top" @submit.prevent="save"><div class="editor-grid"><el-form-item v-for="f in editorFields" :key="f.name" :label="f.label" :class="{wide: ['textarea','json'].includes(f.type)}">
        <el-select v-if="lookupOptions(f.name)" v-model="form[f.name]" filterable clearable :aria-label="f.label"><el-option v-for="o in lookupOptions(f.name)" :key="o.value" :label="o.label" :value="o.value"/></el-select>
        <el-select v-else-if="f.type === 'select'" v-model="form[f.name]" :aria-label="f.label"><el-option v-for="o in f.options" :key="o" :label="optionLabel(f.name,o)" :value="o"/></el-select>
        <el-input-number v-else-if="f.type === 'number'" v-model="form[f.name]" :min="f.name === 'change' ? undefined : 0" :aria-label="f.label" controls-position="right"/>
        <el-input v-else v-model="form[f.name]" :type="['textarea','json'].includes(f.type) ? 'textarea' : f.type === 'password' ? 'password' : 'text'" :rows="f.type === 'json' ? 4 : 5" :show-password="f.type === 'password'" :aria-label="f.label" :placeholder="f.type === 'password' && editing ? '留空保留原密码' : f.type === 'json' ? '请输入有效JSON' : ''"/>
      </el-form-item></div></el-form><template #footer><el-button @click="closeEditor()">取消</el-button><el-button type="primary" :loading="saving" :disabled="!!editing && !formDirty" @click="save">保存修改</el-button></template>
    </el-dialog>
    <el-dialog v-model="deleteOpen" title="确认删除" width="min(530px, 94vw)" class="admin-overlay admin-delete-dialog" :close-on-click-modal="false" :before-close="closeDelete" append-to-body><el-alert title="删除后无法从页面恢复，请核对记录与关联影响。" type="warning" show-icon :closable="false"/><p class="delete-record">{{ deleteTarget?.name || deleteTarget?.title || deleteTarget?.username || deleteTarget?.id || '所选记录' }}</p><p>{{ deletePreview?.note }}</p><ul v-if="deletePreview?.effects.length" class="delete-effects"><li v-for="e in deletePreview.effects" :key="e.label">{{ e.label }}<b>{{ e.count }} 条</b></li></ul><el-checkbox v-model="deleteConfirmed">我已确认删除这条记录及上述关联数据</el-checkbox><template #footer><el-button @click="closeDelete()">取消</el-button><el-button type="danger" :disabled="!deleteConfirmed" :loading="saving" @click="deleteRecord">确认删除</el-button></template></el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, nextTick, ref, shallowRef, watch } from 'vue'
import { useRoute, useRouter, onBeforeRouteUpdate, onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAuthToken, getCurrentUser, removeAuthToken, removeCurrentUser } from '@/utils/authStorage'
import AdminTrend from '@/components/AdminTrend.vue'
import AdminPulse from '@/components/AdminPulse.vue'
import AnimatedNumber from '@/components/AnimatedNumber.vue'
import '@/styles/admin.css'
const route=useRoute(),router=useRouter(),currentUser=getCurrentUser()
const storageKey=`admin-console:${currentUser?.id || 'admin'}:`
function readState(key,fallback){try{return JSON.parse(sessionStorage.getItem(storageKey+key)) ?? fallback}catch{return fallback}}
function storeState(key,value){try{sessionStorage.setItem(storageKey+key,JSON.stringify(value))}catch{}}
const collapsed=ref(readState('collapsed',false)),moduleSearch=ref('')
const modules=ref([]),overview=shallowRef(null),rows=ref([]),lookups=ref({}),recentAudit=shallowRef([]),auditError=ref(''),updatedAt=ref('')
const initializing=ref(true),loading=ref(false),saving=ref(false),exporting=ref(false),preparing=ref(false),previewKey=ref(''),error=ref(''),needsLogin=ref(false)
const search=ref(''),appliedSearch=ref(''),filters=ref({}),appliedFilters=ref({}),visibleColumns=ref([]),page=ref(1),pageSize=ref(20),total=ref(0),days=ref([7,14,30].includes(readState('days',14))?readState('days',14):14)
const moduleId=computed(()=>String(route.params.module || ''))
const currentModule=computed(()=>modules.value.find(m=>m.id===moduleId.value))
const filteredModules=computed(()=>modules.value.filter(m=>`${m.label} ${m.group} ${m.id}`.toLowerCase().includes(moduleSearch.value.trim().toLowerCase())))
const groups=computed(()=>[...new Set(filteredModules.value.map(m=>m.group))])
const moduleIcon=id=>({users:'User',sessions:'Key',runs:'Monitor',states:'Checked',signin:'Calendar',unlocks:'Unlock',classes:'School',members:'UserFilled',tasks:'Document',competitions:'Trophy',problems:'Collection',registrations:'Tickets',submissions:'EditPen',posts:'ChatDotRound',comments:'ChatLineRound',likes:'Star',goods:'Present',points:'Coin',exchanges:'Box',conversations:'Message',messages:'ChatLineRound',friends:'Connection','friend-requests':'Clock',audit:'Document',courses:'Reading',exercises:'Notebook',resources:'FolderOpened'}[id] || 'Grid')
const moduleDescription=computed(()=>({users:'维护用户资料与角色，快速定位需要处理的账号。',runs:'按语言、执行结果和日期定位代码运行记录。',classes:'查看班级归属与教学组织，维护班级基础资料。',tasks:'管理教师题目、代码模板和预期输出。',courses:'维护学习课程，让内容更新清晰有序。',exercises:'管理练习题目，按编程语言快速筛选。',audit:'追踪每一次管理操作，核对修改前后的字段。',points:'保留积分流转记录，通过调整记录修正余额。',posts:'整理论坛内容，管理讨论与置顶状态。'}[moduleId.value] || (moduleId.value?'查看、维护平台数据，每一次修改均保留操作记录。':'从学习活动到教学内容，掌握平台的整体运行情况。')))
const roleLabels={student:'学生',teacher:'教师',admin:'管理员'},actionLabels={create:'新建',update:'修改',delete:'删除'}
const languageLabels={python:'Python',javascript:'JavaScript',java:'Java',cpp:'C++',c:'C'}
function optionLabel(field,value){if(field==='role')return roleLabels[value] || String(value);if(field==='language')return languageLabels[value] || String(value);if(['success','passed','pinned'].includes(field))return Number(value)?{success:'成功',passed:'已通过',pinned:'已置顶'}[field]:{success:'失败',passed:'未通过',pinned:'未置顶'}[field];return ({...actionLabels,pending:'待发货',completed:'已完成',registering:'报名中',ongoing:'进行中',ended:'已结束',general:'常规测试',problem_set:'题目集'})[value] || String(value ?? '—')}
const canEdit=computed(()=>currentModule.value?.fields.some(f=>f.editable))
const availableFields=computed(()=>(currentModule.value?.fields || []).filter(f=>!['textarea','json','password'].includes(f.type) && f.name!=='_rowid'))
const tableFields=computed(()=>availableFields.value.filter(f=>visibleColumns.value.includes(f.name)))
function resetColumns(){visibleColumns.value=availableFields.value.slice(0,8).map(f=>f.name)}
const filterDescription=computed(()=>Object.entries(appliedFilters.value).map(([key,value])=>`${currentModule.value?.filters?.find(f=>f.name===key)?.label || key}：${optionLabel(key,value)}`).join(' · '))
const successRate=computed(()=>overview.value?.runs.total?(overview.value.runs.successful/overview.value.runs.total*100).toFixed(1):'0.0')
const number=n=>Number(n || 0).toLocaleString('zh-CN')
const metrics=computed(()=>[{id:'users',label:'全部用户',value:overview.value?.counts.users,detail:`学生 ${overview.value?.roles.student || 0} · 教师 ${overview.value?.roles.teacher || 0} · 管理员 ${overview.value?.roles.admin || 0}`},{id:'classes',label:'班级总数',value:overview.value?.counts.classes},{id:'tasks',label:'教师题目',value:overview.value?.counts.tasks},{id:'courses',label:'课程总数',value:overview.value?.counts.courses},{id:'competitions',label:'班级测试',value:overview.value?.counts.competitions},{id:'posts',label:'论坛帖子',value:overview.value?.counts.posts}])
const chartColors=['#a889c6','#8ab9ab','#e6ba86','#92accb','#d6a1ba','#c1b1d5']
const languageGradient=computed(()=>{let start=0;return `conic-gradient(${(overview.value?.languages || []).map((l,index)=>{const end=start+l.value/Math.max(1,overview.value.runs.total)*100;const stop=`${chartColors[index%chartColors.length]} ${start}% ${end}%`;start=end;return stop}).join(',') || '#eee8f4 0% 100%'})`})
const formatTime=value=>{if(!value)return '—';const s=String(value).replace(' ','T'),d=new Date(/(?:Z|[+-]\d{2}:?\d{2})$/.test(s)?s:`${s}Z`);return Number.isNaN(d.getTime())?String(value):d.toLocaleString('zh-CN',{timeZone:'Asia/Shanghai'})}
const displayCell=(v,f)=>v==null || v===''?'—':/(?:created_at|updated_at|graded_at|registered_at|joined_at|expires_at)$/.test(f)?formatTime(v):typeof v==='object'?JSON.stringify(v,null,2):String(v)
async function api(path,options={}){const res=await fetch(`/api/admin${path}`,{...options,headers:{'Content-Type':'application/json',Authorization:`Bearer ${getAuthToken()}`,...options.headers}});const data=await res.json().catch(()=>({}));if(!res.ok || data.success===false){if(res.status===401)needsLogin.value=true;throw new Error(typeof data.detail==='string'?data.detail:'操作失败，请检查输入内容或稍后重试')}return data}
function relogin(){removeAuthToken();removeCurrentUser();window.dispatchEvent(new Event('user-updated'));router.push('/login')}
const detailOpen=ref(false),detail=ref(null),detailModule=ref(null),editorOpen=ref(false),editing=ref(null),form=ref({}),formError=ref(''),initialForm=ref('')
const deleteOpen=ref(false),deleteTarget=ref(null),deletePreview=ref(null),deleteConfirmed=ref(false),arrivalKey=ref('')
const editorFields=computed(()=>(currentModule.value?.fields || []).filter(f=>f.editable || (!editing.value && f.createOnly)))
const formDirty=computed(()=>editorOpen.value && JSON.stringify(form.value)!==initialForm.value)
function objectValue(value){try{const parsed=typeof value==='string'?JSON.parse(value):value;return parsed && typeof parsed==='object' && !Array.isArray(parsed)?parsed:{}}catch{return {}}}
const auditChanges=computed(()=>{if(detailModule.value?.id!=='audit')return [];const before=objectValue(detail.value?.before_data),after=objectValue(detail.value?.after_data);const source=modules.value.find(m=>m.id===detail.value?.module);return [...new Set([...Object.keys(before),...Object.keys(after)])].filter(key=>!(/password|hash|token/i.test(key)) && JSON.stringify(before[key])!==JSON.stringify(after[key])).map(name=>({name,label:source?.fields.find(f=>f.name===name)?.label || name,before:displayCell(before[name],name),after:displayCell(after[name],name)}))})
const detailFields=computed(()=>(detailModule.value?.fields || []).filter(f=>f.type!=='password' && !(detailModule.value?.id==='audit' && ['before_data','after_data'].includes(f.name))))
function openDetail(row,id=moduleId.value){detail.value=row;detailModule.value=modules.value.find(m=>m.id===id);detailOpen.value=true}
async function copyValue(value){try{await navigator.clipboard.writeText(typeof value==='object'?JSON.stringify(value,null,2):String(value));ElMessage.success('已复制')}catch{ElMessage.info('复制未完成，可选中文字手动复制')}}
const viewCache=new Map()
const contentElement=ref(null),scrollFloor=ref(0)
let pendingScroll=null,activeViewId=moduleId.value
let requestVersion=0,moduleRevision=0,readController,lookupController,previewController,exportController,arrivalTimer,disposed=false
function snapshot(){return {search:search.value,appliedSearch:appliedSearch.value,filters:filters.value,appliedFilters:appliedFilters.value,columns:visibleColumns.value,page:page.value,pageSize:pageSize.value,scroll:pendingScroll?.id===activeViewId && !pendingScroll.cancelled ? pendingScroll.top : window.scrollY}}
function rememberView(id=activeViewId){if(!modules.value.length)return;const state=snapshot(),key=id || 'overview';storeState(`view:${key}`,state);viewCache.set(key,{...JSON.parse(JSON.stringify(state)),rows:rows.value,total:total.value})}
function cleanFilters(values){return Object.fromEntries((currentModule.value?.filters || []).filter(f=>values?.[f.name]!=='' && values?.[f.name]!=null).map(f=>[f.name,values[f.name]]))}
function restoreView(fallbackScroll=window.scrollY){const state=viewCache.get(moduleId.value) || readState(`view:${moduleId.value}`,{});search.value=state.search || '';appliedSearch.value=state.appliedSearch || '';filters.value=cleanFilters(state.filters);appliedFilters.value=cleanFilters(state.appliedFilters);page.value=Math.max(1,Number(state.page) || 1);pageSize.value=[10,20,50,100].includes(state.pageSize)?state.pageSize:20;visibleColumns.value=(state.columns || []).filter(name=>availableFields.value.some(f=>f.name===name));if(!visibleColumns.value.length)resetColumns();rows.value=state.rows || [];total.value=state.total || 0;
  if(Object.keys(route.query).length){filters.value={};appliedFilters.value={};search.value='';appliedSearch.value='';page.value=1}
  if(route.query.q!=null){search.value=appliedSearch.value=String(route.query.q);page.value=1}
  for(const f of currentModule.value?.filters || []){if(route.query[f.name]!=null){const raw=String(route.query[f.name]);filters.value[f.name]=f.type==='date'?raw:f.options.find(value=>String(value)===raw);appliedFilters.value=cleanFilters(filters.value);page.value=1}}
  return Number.isFinite(state.scroll)?Math.max(0,state.scroll):fallbackScroll
}
function queryString(){return new URLSearchParams({page:String(page.value),pageSize:String(pageSize.value),q:appliedSearch.value,filters:JSON.stringify(appliedFilters.value)}).toString()}
async function loadRows(){if(!currentModule.value)return;readController?.abort();const controller=readController=new AbortController(),version=++requestVersion,id=moduleId.value;loading.value=true;error.value='';try{const data=await api(`/data/${id}?${queryString()}`,{signal:controller.signal});if(version!==requestVersion || disposed)return;rows.value=data.items;total.value=data.total;updatedAt.value=new Date().toISOString();const lastPage=Math.max(1,Math.ceil(total.value/pageSize.value));if(page.value>lastPage){page.value=lastPage;return await loadRows()}rememberView(id)}catch(e){if(e.name!=='AbortError' && version===requestVersion)error.value=e.message}finally{if(version===requestVersion)loading.value=false}}
function updateOverview(data){
  const {generatedAt,...snapshot}=data,previous=overview.value || {}
  let changed=Object.keys(snapshot).length!==Object.keys(previous).length
  for(const key of Object.keys(snapshot)){
    if(JSON.stringify(snapshot[key])===JSON.stringify(previous[key]))snapshot[key]=previous[key]
    else changed=true
  }
  if(changed)overview.value=snapshot
  updatedAt.value=generatedAt
}
async function loadOverview(){readController?.abort();const controller=readController=new AbortController(),version=++requestVersion;loading.value=true;error.value='';try{const [data,audit]=await Promise.allSettled([api(`/overview?days=${days.value}`,{signal:controller.signal}),api('/data/audit?page=1&pageSize=5',{signal:controller.signal})]);if(version!==requestVersion || disposed)return;if(data.status==='rejected')throw data.reason;updateOverview(data.value);auditError.value=audit.status==='rejected'?'操作记录暂时无法加载，刷新后重试。':'';const auditItems=audit.status==='fulfilled'?audit.value.items:[];if(JSON.stringify(recentAudit.value)!==JSON.stringify(auditItems))recentAudit.value=auditItems}catch(e){if(e.name!=='AbortError' && version===requestVersion)error.value=e.message}finally{if(version===requestVersion)loading.value=false}}
function requestRefresh(){if(loading.value || initializing.value)return;return refresh()}
function refresh(){if(!modules.value.length && !initializing.value)return initialize();return moduleId.value?loadRows():loadOverview()}
function searchRecords(){page.value=1;appliedSearch.value=search.value.trim();appliedFilters.value=cleanFilters(filters.value);return loadRows()}
function changePageSize(){page.value=1;return loadRows()}
function resetSearch(){search.value='';filters.value={};return searchRecords()}
function openDay(day){router.push({path:'/admin/runs',query:{day}})}
function openLanguage(language){router.push({path:'/admin/runs',query:{language}})}
async function openEditor(row=null){if(preparing.value || saving.value)return;const revision=moduleRevision;preparing.value=true;lookupController?.abort();const controller=lookupController=new AbortController();try{const data=await api('/lookups',{signal:controller.signal});if(revision!==moduleRevision || disposed)return;lookups.value=data;editing.value=row;formError.value='';form.value={};for(const f of editorFields.value){let v=row?.[f.name];if(v==null)v=f.type==='number'?0:f.type==='json'?['daily_checkin','practice_done','exercise_metadata'].includes(f.name)?'{}':'[]':'';if(f.type==='number')v=Number(v) || 0;if(f.type==='json' && typeof v!=='string')v=JSON.stringify(v,null,2);form.value[f.name]=v}if(!row && moduleId.value==='users')form.value.role='student';if(!row && moduleId.value==='posts'){form.value.category='ai';form.value.pinned=0}if(!row && moduleId.value==='tasks')form.value.language='python';initialForm.value=JSON.stringify(form.value);editorOpen.value=true}catch(e){if(e.name!=='AbortError' && revision===moduleRevision)ElMessage.error(e.message)}finally{if(revision===moduleRevision)preparing.value=false}}
function lookupOptions(field) {
  if(['teacher_id','student_id','user_id'].includes(field)) { const role=field==='teacher_id' ? 'teacher' : field==='student_id' ? 'student' : null; return (lookups.value.users || []).filter(u => !role || u.role===role).map(u => ({value:u.id,label:`${u.name || u.username} · ${u.username} (${roleLabels[u.role]})`})) }
  if(field==='class_id') return (lookups.value.classes || []).map(c=>({value:c.id,label:c.name}))
  if(field==='competition_id') return (lookups.value.competitions || []).map(c=>({value:c.id,label:c.name}))
  if(field==='task_id') return (lookups.value.tasks || []).map(t=>({value:t.id,label:t.title}))
  return null
}
async function confirmDiscard(){if(!formDirty.value)return true;try{await ElMessageBox.confirm('当前记录尚未保存，离开后会丢失本次修改。','放弃修改？',{confirmButtonText:'放弃修改',cancelButtonText:'继续编辑',type:'warning'});return true}catch{return false}}
async function closeEditor(done){if(saving.value)return;if(await confirmDiscard()){editorOpen.value=false;if(typeof done==='function')done()}}
function closeDelete(done){if(saving.value)return;deleteOpen.value=false;if(typeof done==='function')done()}
async function mayLeave(){if(saving.value){ElMessage.info('正在提交，请稍候');return false}return confirmDiscard()}
onBeforeRouteUpdate(mayLeave)
onBeforeRouteLeave(mayLeave)
async function save(){if(saving.value)return;const id=moduleId.value,revision=moduleRevision,row=editing.value;saving.value=true;formError.value='';try{const payload={};for(const f of editorFields.value){let v=form.value[f.name];if(f.type==='password' && !v)continue;if(!row && v==='' && !['expectedOutput','starterCode','solutionCode','expected_output','starter_code','solution_code'].includes(f.name))continue;if(f.type==='json'){try{v=JSON.parse(v)}catch{throw new Error(`${f.label}需要有效JSON`)}}payload[f.name]=v}const data=await api(`/data/${id}${row?`/${row._key}`:''}`,{method:row?'PUT':'POST',body:JSON.stringify(payload)});if(revision!==moduleRevision || disposed)return;editorOpen.value=false;initialForm.value=JSON.stringify(form.value);ElMessage.success('已保存，变更已记录');arrivalKey.value=data.key || row?._key || '';clearTimeout(arrivalTimer);arrivalTimer=setTimeout(()=>arrivalKey.value='',2200);await loadRows()}catch(e){if(revision===moduleRevision && !disposed)formError.value=e.message}finally{saving.value=false}}
async function prepareDelete(row){if(previewKey.value || saving.value)return;const revision=moduleRevision;previewController?.abort();const controller=previewController=new AbortController();previewKey.value=row._key;try{const preview=await api(`/data/${moduleId.value}/${row._key}/delete-preview`,{signal:controller.signal});if(revision!==moduleRevision || disposed)return;deletePreview.value=preview;deleteTarget.value=row;deleteConfirmed.value=false;deleteOpen.value=true}catch(e){if(e.name!=='AbortError' && revision===moduleRevision)ElMessage.error(e.message)}finally{if(revision===moduleRevision)previewKey.value=''}}
async function deleteRecord(){if(!deleteConfirmed.value || saving.value)return;const id=moduleId.value,key=deleteTarget.value._key,revision=moduleRevision;saving.value=true;try{await api(`/data/${id}/${key}`,{method:'DELETE'});if(revision!==moduleRevision || disposed)return;deleteOpen.value=false;ElMessage.success(id==='sessions'?'已注销会话':'已删除');if(rows.value.length===1 && page.value>1)page.value--;await loadRows()}catch(e){if(revision===moduleRevision && !disposed)ElMessage.error(e.message)}finally{saving.value=false}}
function tableRowClass({row}){return row._key===arrivalKey.value?'admin-row-arrived':''}
async function exportCsv(){if(exporting.value)return;const id=moduleId.value,label=currentModule.value.label;exporting.value=true;const controller=exportController=new AbortController();try{const res=await fetch(`/api/admin/export/${id}?${queryString()}`,{headers:{Authorization:`Bearer ${getAuthToken()}`},signal:controller.signal});if(!res.ok){const data=await res.json();if(res.status===401)needsLogin.value=true;throw new Error(data.detail || '导出失败')}const url=URL.createObjectURL(await res.blob()),a=document.createElement('a');a.href=url;a.download=`${label}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}catch(e){if(e.name!=='AbortError')ElMessage.error(e.message)}finally{exporting.value=false}}
function beforeUnload(event){if(formDirty.value || saving.value){event.preventDefault();event.returnValue=''}}
watch(collapsed,value=>storeState('collapsed',value))
watch(days,value=>storeState('days',value))
watch(visibleColumns,()=>{if(!initializing.value)rememberView()},{deep:true})
function beginScrollRestore(top){
  const element=contentElement.value,contentTop=(element?.getBoundingClientRect().top || 0)+window.scrollY
  // Keep the outgoing height while the incoming list is empty; otherwise the browser clamps scrollY.
  scrollFloor.value=Math.max(450,element?.offsetHeight || 0,top+window.innerHeight-contentTop)
  const pending={id:moduleId.value,revision:moduleRevision,top:Math.max(0,top),cancelled:false}
  pendingScroll=pending
  return pending
}
function applyScroll(pending){
  if(disposed || pendingScroll!==pending || pending.cancelled)return
  if(Math.abs(window.scrollY-pending.top)>1)window.scrollTo({top:pending.top,behavior:'instant'})
}
async function finishScrollRestore(pending){
  await nextTick()
  await new Promise(resolve=>requestAnimationFrame(resolve))
  if(disposed || pendingScroll!==pending)return
  scrollFloor.value=0
  await nextTick()
  applyScroll(pending)
  pendingScroll=null
  rememberView()
}
function stopScrollRestore(event){
  if(event.type==='keydown' && !['ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' '].includes(event.key))return
  if(event.type==='keydown' && event.target?.closest('input,textarea,select,[contenteditable="true"]'))return
  if(pendingScroll)pendingScroll.cancelled=true
}
async function switchModule(to,from){
  const previousScroll=window.scrollY
  rememberView(from)
  activeViewId=to
  moduleRevision++;requestVersion++;readController?.abort();lookupController?.abort();previewController?.abort()
  editorOpen.value=false;detailOpen.value=false;deleteOpen.value=false;preparing.value=false;previewKey.value='';error.value=''
  if(!modules.value.length)return
  if(to && !currentModule.value){router.replace('/admin');return}
  const storedOverview=viewCache.get('overview') || readState('view:overview',{})
  const target=to===from?previousScroll:to?restoreView(previousScroll):Number.isFinite(storedOverview.scroll)?storedOverview.scroll:previousScroll
  // Query changes keep the reading position while still applying the new filters.
  if(to && to===from)restoreView(previousScroll)
  const pending=beginScrollRestore(target)
  await nextTick()
  if(disposed || pendingScroll!==pending)return
  applyScroll(pending)
  await refresh()
  await finishScrollRestore(pending)
}
watch(()=>[moduleId.value,route.query],([to],[from])=>switchModule(to,from))
async function initialize(){
  initializing.value=true;error.value=''
  try{
    const [m,l]=await Promise.allSettled([api('/modules'),api('/lookups')])
    if(disposed)return
    if(m.status==='rejected')throw m.reason
    modules.value=m.value.modules
    if(l.status==='fulfilled')lookups.value=l.value
    if(moduleId.value && !currentModule.value){await router.replace('/admin');return}
    const saved=readState('view:overview',{})
    const top=moduleId.value?restoreView():Number.isFinite(saved.scroll)?saved.scroll:window.scrollY
    const pending=beginScrollRestore(top)
    await nextTick()
    applyScroll(pending)
    await refresh()
    await finishScrollRestore(pending)
  }catch(e){if(!disposed)error.value=e.message}finally{initializing.value=false}
}
onMounted(()=>{
  window.addEventListener('beforeunload',beforeUnload)
  window.addEventListener('wheel',stopScrollRestore,{passive:true})
  window.addEventListener('touchstart',stopScrollRestore,{passive:true})
  window.addEventListener('keydown',stopScrollRestore)
  initialize()
})
onBeforeUnmount(()=>{rememberView();disposed=true;pendingScroll=null;window.removeEventListener('wheel',stopScrollRestore);window.removeEventListener('touchstart',stopScrollRestore);window.removeEventListener('keydown',stopScrollRestore);requestVersion++;readController?.abort();lookupController?.abort();previewController?.abort();exportController?.abort();clearTimeout(arrivalTimer);window.removeEventListener('beforeunload',beforeUnload)})
</script>
