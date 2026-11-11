export function conversationHistory(messages) {
  return messages.filter(item=>!item.error && ['user','assistant','ai'].includes(item.role || item.from) && String(item.fullContent || item.content || '').trim()).slice(-8).map(item=>({role:(item.role || item.from)==='user'?'user':'assistant',content:String(item.fullContent || item.content).slice(0,1600)}))
}
export async function requestAssistant(message, context, history, { signal } = {}) {
  const controller=new AbortController(),abort=()=>controller.abort()
  let timedOut=false
  if(signal?.aborted)abort()
  signal?.addEventListener('abort',abort,{once:true})
  const timer=setTimeout(()=>{timedOut=true;controller.abort()},65000)
  try{
    const response=await fetch('/api/ai/chat',{method:'POST',signal:controller.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({message,context,history})})
    const data=await response.json().catch(()=>({}))
    if(!response.ok || data.success===false || data.error)throw new Error(data.message || data.detail || '助手暂时不可用，请重试')
    if(typeof data.reply!=='string' || !data.reply.trim())throw new Error('助手没有返回有效内容，请重试')
    return data
  }catch(error){
    if(timedOut)throw new Error('助手响应超时，请稍后重试。')
    if(signal?.aborted)throw new DOMException('请求已取消','AbortError')
    if(error instanceof TypeError)throw new Error('暂时无法连接编程助手，请稍后重试。')
    throw error
  }finally{clearTimeout(timer);signal?.removeEventListener('abort',abort)}
}
