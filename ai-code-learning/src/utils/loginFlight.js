export async function flyLoginToAvatar(source,navigate){
  const target=document.querySelector('[data-user-avatar]')
  const go=()=>navigate?.()
  if(!source?.isConnected || !target || typeof source.animate!=='function')return go()
  const start=source.getBoundingClientRect(),end=target.getBoundingClientRect()
  if(!start.width || !start.height || !end.width || !end.height)return go()
  const card=source.cloneNode(true)
  // The temporary visual never contains credentials or interactive controls.
  card.querySelectorAll('input,textarea,select,script').forEach(node=>node.remove())
  for(const node of [card,...card.querySelectorAll('*')]){
    node.removeAttribute('id');node.removeAttribute('autofocus')
    node.style.animation='none';node.style.transition='none'
  }
  card.setAttribute('aria-hidden','true');card.inert=true
  Object.assign(card.style,{position:'fixed',left:`${start.left}px`,top:`${start.top}px`,width:`${start.width}px`,height:`${start.height}px`,maxWidth:'none',margin:'0',zIndex:'3000',pointerEvents:'none',overflow:'hidden',transformOrigin:'0 0',borderRadius:'18px',willChange:'transform, opacity',boxShadow:'0 18px 55px #3e275a30'})
  document.body.append(card)
  card.querySelectorAll('svg').forEach(svg=>{try{svg.pauseAnimations?.()}catch{}})
  const visibility=source.style.visibility
  source.style.visibility='hidden'
  try{
    // Mount and paint the destination underneath the snapshot before starting its flight.
    await go()
    if(!document.hidden)await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))
    const destination=target.isConnected?target.getBoundingClientRect():end
    const scale=Math.min(destination.width/start.width,destination.height/start.height)
    const dx=destination.left+destination.width/2-start.left-start.width*scale/2
    const dy=destination.top+destination.height/2-start.top-start.height*scale/2
    const finish=`translate3d(${dx}px,${dy}px,0) scale(${scale})`
    const flight=card.animate([{transform:'translate3d(0,0,0) scale(1)',opacity:1},{transform:finish,opacity:.95,offset:.86},{transform:finish,opacity:0}],{duration:640,easing:'cubic-bezier(.4,0,.2,1)',fill:'forwards'})
    await flight.finished.catch(()=>{})
    if(target.isConnected)target.animate([{transform:'scale(.94)'},{transform:'scale(1.06)'},{transform:'scale(1)'}],{duration:260,easing:'ease-out'})
  }finally{
    if(source.isConnected)source.style.visibility=visibility
    card.remove()
  }
}
