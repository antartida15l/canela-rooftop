import {useEffect} from 'react';

export function usePageMotion(refreshKey:string){
 useEffect(()=>{
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
  if(reduced.matches||!('IntersectionObserver' in window))return;
  const observer=new IntersectionObserver(entries=>{for(const e of entries)if(e.isIntersecting){e.target.classList.add('is-revealed');observer.unobserve(e.target)}},{threshold:0.08,rootMargin:'0px 0px -25px 0px'});
  const selector='.section-heading,.experience-copy,.experience-art,.signature-card,.product-card,.gallery-item,.reserve-copy,.reservation-form,.location>div,.moments-copy,.moment-scene,.ritual-intro,.ritual-step,.social-copy,.social-poster';
  document.querySelectorAll<HTMLElement>(selector).forEach((el,i)=>{if(!el.hasAttribute('data-reveal')){el.setAttribute('data-reveal','');el.style.setProperty('--reveal-delay',`${(i%3)*75}ms`)}if(!el.classList.contains('is-revealed'))observer.observe(el)});
  return()=>observer.disconnect();
 },[refreshKey]);
 useEffect(()=>{
  let frame=0;const update=()=>{const max=document.documentElement.scrollHeight-window.innerHeight;document.documentElement.style.setProperty('--page-progress',`${max>0?Math.min(100,window.scrollY/max*100):0}%`);frame=0};
  const onScroll=()=>{if(!frame)frame=requestAnimationFrame(update)};
  window.addEventListener('scroll',onScroll,{passive:true});window.addEventListener('resize',onScroll);update();
  return()=>{window.removeEventListener('scroll',onScroll);window.removeEventListener('resize',onScroll);cancelAnimationFrame(frame)};
 },[]);
}
