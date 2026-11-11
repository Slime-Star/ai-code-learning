import {onBeforeUnmount,ref} from 'vue'
import {useRouter} from 'vue-router'

export function useRouteFeedback(){
  const router=useRouter()
  const pending=ref(false),error=ref(''),destination=ref('')
  let currentTarget='',timer
  const stopStart=router.beforeEach(to=>{
    currentTarget=to.fullPath
    error.value=''
    clearTimeout(timer)
    timer=setTimeout(()=>{pending.value=true},160)
  })
  const stopEnd=router.afterEach(to=>{
    if(to.fullPath!==currentTarget)return
    clearTimeout(timer);pending.value=false
  })
  const stopError=router.onError((cause,to)=>{
    if(to && to.fullPath!==currentTarget)return
    clearTimeout(timer)
    pending.value=false
    destination.value=to?.fullPath || currentTarget || router.currentRoute.value.fullPath
    error.value='页面暂时无法加载，请检查连接后重新打开。'
    console.error('页面导航失败',cause)
  })
  function retry(){window.location.assign(router.resolve(destination.value || currentTarget || '/').href)}
  onBeforeUnmount(()=>{clearTimeout(timer);stopStart();stopEnd();stopError()})
  return {pending,error,retry}
}
