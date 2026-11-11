<template>
  <div class="forum-container" @click.passive>
    <div class="login-tip-bar">
      <span v-if="!isLogin" class="tip-text">🔒 请先登录后发布/删除帖子</span>
      <span v-else class="tip-text">👋 欢迎你，<strong>{{ currentUser }}</strong>！</span>
      <el-button
        v-if="!isLogin"
        type="primary"
        size="small"
        @click="goToLogin"
        class="login-btn"
      >
        去登录
      </el-button>
      
    </div>

    <div class="forum-intro">
    <div class="post-create">
      <div class="post-create-title">📝 发布新讨论</div>
      <form class="post-form" @submit.prevent="handlePost">
        <div class="form-row">
          <input
            v-model="postForm.title"
            type="text"
            class="post-title"
            placeholder="请输入帖子标题"
            :disabled="!isLogin"
          >
          <select
            v-model="postForm.category"
            class="post-category"
            :disabled="!isLogin"
          >
            <option value="">选择帖子分类</option>
            <option value="ai">AI辅助编程</option>
            <option value="code">代码求助</option>
            <option value="share">经验分享</option>
          </select>
        </div>
        <textarea
          v-model="postForm.content"
          class="post-content"
          placeholder="请详细描述你的问题/分享的内容..."
          :disabled="!isLogin"
        ></textarea>
        <div class="post-actions">
          <button type="button" class="btn btn-cancel" @click="resetForm" :disabled="!isLogin">取消</button>
          <button type="submit" class="btn btn-post" :disabled="busy || !isLogin || !postForm.title || !postForm.category || !postForm.content">发布帖子</button>
        </div>
      </form>
    </div>
    <aside class="forum-game-side" aria-label="休息一下，符号配对"><WhitespaceGame scene="chat" game="memory" compact /></aside>
    </div>

    <div class="forum-categories">
      <div
        v-for="tag in categoryTags"
        :key="tag.id"
        :class="['category-tag', { active: activeTagId === tag.id }]"
        @click.stop="activeTagId = tag.id"
      >
        {{ tag.name }}
      </div>
    </div>

    <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon/>
    <el-alert v-if="legacyCount" type="info" :closable="false"><template #title>发现 {{ legacyCount }} 条旧版浏览器帖子，可导入你自己发布的内容。</template><el-button :loading="busy" @click="importLegacy">导入旧帖子</el-button></el-alert>
    <div class="posts-list" v-loading="loading">
      <div v-if="filteredPosts.length === 0" class="empty-post">
        暂无相关帖子，快来发布第一条吧！
      </div>

      <div
        v-for="post in filteredPosts"
        :key="post.id"
        class="post-card"
      >
        <div class="post-header">
          <div class="post-author">
            <div class="author-avatar">{{ post.avatarText }}</div>
            <div class="author-info">
              <div class="author-name">{{ post.author }}</div>
              <div class="post-time">{{ post.createTime }}</div>
            </div>
          </div>
          <div class="post-tag">{{ post.tag }}</div>
        </div>

        <div class="post-body">
          <div class="post-title-text">{{ post.title }}</div>
          <div class="post-content-text">{{ post.content }}</div>
        </div>

        <!-- 评论列表 -->
        <div class="comment-section" v-if="post.comments && post.comments.length">
          <div class="comment-title">评论 ({{ post.comments.length }})</div>
          <div class="comment-list">
            <div class="comment-item" v-for="(c, idx) in post.comments" :key="idx">
              <div class="comment-line">
                <div class="comment-main">
                  <div class="comment-user">{{ c.user }}</div>
                  <div class="comment-content">{{ c.content }}</div>
                  <div class="comment-time">{{ c.time }}</div>
                </div>
                <button
                  v-if="isLogin && (isTeacher || c.user_id === currentUserId)"
                  class="comment-delete-btn"
                  @click.stop="handleDeleteComment(post.id, idx)"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 回复输入框 -->
        <MotionReveal :open="isLogin && showReplyBox === post.id">
        <div class="comment-input-box">
          <textarea
            :id="`comment-input-${post.id}`"
            v-model="replyContent[post.id]"
            placeholder="输入你的评论..."
            class="comment-input"
          ></textarea>
          <button class="comment-submit-btn" @click.stop="submitComment(post.id)">
            发表
          </button>
        </div>
        </MotionReveal>

        <!-- 底部栏：回复 + 点赞 + 删除 -->
        <div class="post-footer">
          <div class="post-actions-btn">
            <span class="action-btn" @click.stop="handleReply(post.id)">回复</span>
            <span
              class="action-btn like-btn"
              :class="{ liked: post.isLiked }"
              @click.stop="handleLike(post.id)"
            >
              ♥ 
            </span>
          </div>
          <div v-if="isLogin && (isTeacher || currentUserId === post.authorId)" class="post-delete">
            <button class="delete-btn" @click.stop="handleDelete(post.id)">
              🗑️ 删除
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="forum-bottom-scene"><CodeLandscape class="forum-bottom-art" variant="planet" /><AnimatedCompanion class="forum-paper-plane" kind="plane" /></div>
    <CodeTicker reverse />
  </div>
</template>

<script setup>
import WhitespaceGame from '@/components/WhitespaceGame.vue'
import AnimatedCompanion from '@/components/AnimatedCompanion.vue'
import CodeLandscape from '@/components/CodeLandscape.vue'
import CodeTicker from '@/components/CodeTicker.vue'
import MotionReveal from '@/components/MotionReveal.vue'
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCurrentUser, getAuthToken } from '@/utils/authStorage'
const router = useRouter()
const user = getCurrentUser()
const isLogin = ref(!!user), currentUser = ref(user?.name || ''), currentUserId = user?.id
const isTeacher = ref(['teacher','admin'].includes(user?.role))
const replyContent = ref({}), showReplyBox = ref(null), postList = ref([]), loading = ref(false), busy = ref(false), loadError = ref('')
const postForm = ref({title:'',category:'',content:''})
const categoryTags = ref([{id:1,name:'全部讨论',value:'all'},{id:2,name:'AI辅助编程',value:'ai'},{id:3,name:'代码求助',value:'code'},{id:4,name:'经验分享',value:'share'}])
const activeTagId = ref(1)
const filteredPosts = computed(() => { const tag=categoryTags.value.find(t=>t.id===activeTagId.value); return tag?.value==='all' ? postList.value : postList.value.filter(p=>p.category===tag?.value) })
const legacyPosts=ref([])
try { const old=JSON.parse(localStorage.getItem('forumPosts') || '[]'); if(Array.isArray(old)) legacyPosts.value=old.filter(p=>Number(p.id)>5 && p.author===currentUser.value) } catch {}
const legacyCount=computed(()=>legacyPosts.value.length)
const goToLogin = () => router.push('/login')
async function api(path, method='GET', body) {
  const headers={'Content-Type':'application/json'}
  if(getAuthToken()) headers.Authorization=`Bearer ${getAuthToken()}`
  const response=await fetch(`/api/forum${path}`,{method,headers,body:body ? JSON.stringify(body) : undefined})
  const data=await response.json().catch(()=>({}))
  if(!response.ok) throw new Error(typeof data.detail==='string' ? data.detail : '操作失败，请稍后重试')
  return data
}
async function loadPosts() { loading.value=true; loadError.value=''; try { postList.value=(await api('/posts')).posts } catch(e) { loadError.value=e.message } finally { loading.value=false } }
const resetForm = () => { postForm.value={title:'',category:'',content:''} }
async function handlePost() {
  if(!isLogin.value) return ElMessage.warning('请先登录')
  if(busy.value) return
  busy.value=true
  try { await api('/posts','POST',postForm.value); resetForm(); await loadPosts(); ElMessage.success('发布成功') } catch(e) { ElMessage.error(e.message) } finally { busy.value=false }
}
function handleReply(id) { if(!isLogin.value) return ElMessage.warning('请先登录后再评论'); showReplyBox.value=id; if(replyContent.value[id]===undefined) replyContent.value[id]=''; nextTick(()=>document.getElementById(`comment-input-${id}`)?.focus()) }
async function handleLike(id) { if(!isLogin.value) return ElMessage.warning('请先登录后点赞'); if(busy.value) return; busy.value=true; try { await api(`/posts/${id}/like`,'POST'); await loadPosts() } catch(e) { ElMessage.error(e.message) } finally { busy.value=false } }
async function submitComment(id) { const content=(replyContent.value[id] || '').trim(); if(!content) return ElMessage.warning('请输入评论'); if(busy.value) return; busy.value=true; try { await api(`/posts/${id}/comments`,'POST',{content}); replyContent.value[id]=''; showReplyBox.value=null; await loadPosts(); ElMessage.success('评论成功') } catch(e) { ElMessage.error(e.message) } finally { busy.value=false } }
async function remove(kind,id) { try { await ElMessageBox.confirm('删除后无法恢复，确认删除？','删除确认',{type:'warning'}); await api(`/${kind}/${id}`,'DELETE'); await loadPosts(); ElMessage.success('已删除') } catch(e) { if(e instanceof Error) ElMessage.error(e.message) } }
const handleDelete = id => remove('posts',id)
const handleDeleteComment = (id,index) => { const comment=postList.value.find(p=>p.id===id)?.comments[index]; if(comment) remove('comments',comment.id) }
async function importLegacy() { busy.value=true; try { const data=await api('/import-legacy','POST',{posts:legacyPosts.value}); legacyPosts.value=[]; await loadPosts(); ElMessage.success(`已导入 ${data.imported} 条帖子`) } catch(e) { ElMessage.error(e.message) } finally { busy.value=false } }
onMounted(loadPosts)
</script>

<style scoped>
.forum-game-side { position: relative; }
.forum-bottom-scene { position: relative; max-width: 1100px; margin: 0 auto; }
.forum-paper-plane { position: absolute; right: 8%; bottom: 30px; width: 110px; opacity: .85; }
@media (max-width: 900px) { .forum-paper-plane { display: none; } }
.forum-intro { width: 90%; max-width: 1200px; margin: 0 auto 24px; display: grid; grid-template-columns: minmax(0,1fr) 220px; gap: 24px; align-items: center; }
.forum-intro .post-create { width: 100%; min-width: 0; margin: 0; }
.forum-game-side { padding: 10px 16px; border-left: 1px solid #e8e0f1; min-width: 0; }
.forum-bottom-art { margin: 16px auto; }
@media (max-width: 900px) { .forum-intro { grid-template-columns: minmax(0,1fr); gap: 16px; }.forum-game-side { width: 100%; max-width: 330px; justify-self: end; border: 0; padding: 0 8px; }.forum-game-side :deep(.micro-game) { flex-direction: row; }.forum-game-side :deep(.micro-copy) { width: 140px; } }
@media (max-width: 480px) { .forum-game-side { max-width: 100%; padding: 0; }.forum-game-side :deep(.micro-game) { gap: 10px; }.forum-game-side :deep(.micro-copy) { width: auto; flex: 1; min-width: 0; }.forum-intro .form-row { flex-wrap: wrap; }.forum-intro .post-title { min-width: 0; width: 100%; }.forum-intro .post-category { width: 100%; } }
.login-tip-bar {
  width: 90%;
  max-width: 1200px;
  margin: 0 auto 16px;
  padding: 10px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-sizing: border-box;
}
.tip-text {
  font-size: 14px;
  color: #666;
}
.login-btn, .logout-btn {
  padding: 4px 12px !important;
  height: auto !important;
}

.forum-container {
  width: 100%;
  margin: 20px auto;
  padding: 0 20px;
  font-family: "Microsoft YaHei", sans-serif;
}

.post-create {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  width: 90%;
  max-width: 1200px;
  margin: 0 auto 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  box-sizing: border-box;
}
.post-create-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #667eea;
}
.post-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.form-row {
  display: flex;
  gap: 12px;
}
.post-title {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
}
.post-title:disabled { background: #f5f5f5; }
.post-category {
  width: 180px;
  padding: 10px 16px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
}
.post-category:disabled { background: #f5f5f5; }
.post-content {
  height: 120px;
  padding: 16px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  resize: none;
}
.post-content:disabled { background: #f5f5f5; }
.post-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
.btn {
  padding: 8px 20px;
  border-radius: 4px;
  border: none;
}
.btn:disabled { background: #ccc !important; }
.btn-cancel { background: #f5f5f5; color: #666; }
.btn-post { background: #667eea; color: #fff; }

.forum-categories {
  display: flex;
  gap: 8px;
  width: 90%;
  max-width: 1200px;
  margin: 0 auto 24px;
}
.category-tag {
  padding: 6px 16px;
  background: #e6e9ff;
  color: #667eea;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
}
.category-tag.active {
  background: #667eea;
  color: #fff;
}

.posts-list {
  width: 90%;
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.empty-post {
  padding: 40px;
  background: #fff;
  border-radius: 8px;
  color: #999;
  text-align: center;
}
.post-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.post-author {
  display: flex;
  align-items: center;
  gap: 10px;
}
.author-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667eea;
}
.author-name { font-size: 14px; color: #333; }
.post-time { font-size: 12px; color: #999; }
.post-tag {
  padding: 2px 8px;
  background: #f6ffed;
  color: #52c41a;
  border-radius: 4px;
  font-size: 12px;
}
.post-title-text {
  font-size: 18px;
  font-weight: 600;
  color: #667eea;
  margin-bottom: 8px;
}
.post-content-text {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* 评论区 */
.comment-section {
  margin: 12px 0;
  padding-top: 12px;
  border-top: 1px dashed #eee;
}
.comment-title {
  font-size: 14px;
  color: #667eea;
  margin-bottom: 8px;
}
.comment-item {
  background: #f7f8fa;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  margin-bottom: 6px;
}
.comment-line {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.comment-main {
  flex: 1;
}
.comment-delete-btn {
  background: transparent;
  border: none;
  color: #f56c6c;
  font-size: 12px;
  cursor: pointer;
  padding: 2px 6px;
}
.comment-user { color: #667eea; font-weight: bold; }
.comment-content { margin: 4px 0; }
.comment-time { font-size: 12px; color: #999; text-align: right; }

.comment-input-box {
  display: flex;
  gap: 8px;
  margin:12px 0;
}
.comment-input {
  flex:1;
  height:60px;
  border:1px solid #eee;
  border-radius:6px;
  padding:8px;
  resize:none;
}
.comment-submit-btn {
  background:#667eea;
  color:#fff;
  border:none;
  border-radius:4px;
  padding:8px 12px;
}

/* 底部栏：回复 + 点赞 + 删除（布局调整） */
.post-footer {
  padding-top:12px;
  border-top:1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.post-actions-btn {
  display:flex;
  gap:20px;
}
.action-btn {
  font-size:14px;
  color:#666;
  cursor:pointer;
  transition:all 0.3s ease;
}
.like-btn.liked {
  color:#f56c6c;
  animation: likeBounce 0.4s ease;
}
@keyframes likeBounce {
  0%{transform:scale(1)}
  50%{transform:scale(1.2)}
  100%{transform:scale(1)}
}
.delete-btn {
  background: #fef0f0;
  color: #f56c6c;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

@media (max-width:768px){
  .form-row{flex-direction:column}
  .post-category{width:100%}
}
</style>
