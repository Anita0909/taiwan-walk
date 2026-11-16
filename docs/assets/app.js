(() => {
 const gallery=document.querySelector('.gallery');
 if(gallery){
  const slides=[...gallery.querySelectorAll('.slide')];
  const status=document.querySelector('#gallery-status');
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const current=()=>slides.reduce((best,slide,i)=>Math.abs(slide.offsetLeft-gallery.scrollLeft-gallery.offsetLeft)<Math.abs(slides[best].offsetLeft-gallery.scrollLeft-gallery.offsetLeft)?i:best,0);
  const move=(step)=>{const next=Math.max(0,Math.min(slides.length-1,current()+step));gallery.scrollTo({left:slides[next].offsetLeft-slides[0].offsetLeft,behavior:reduced?'instant':'smooth'});};
  document.querySelector('#previous').addEventListener('click',()=>move(-1));
  document.querySelector('#next').addEventListener('click',()=>move(1));
  gallery.addEventListener('keydown',e=>{if(e.target!==gallery)return;if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();move(e.key==='ArrowRight'?1:-1);}});
  gallery.addEventListener('scroll',()=>{status.textContent=`${current()+1} / ${slides.length}`;},{passive:true});
 }
 const search=document.querySelector('#search'),region=document.querySelector('#region');
 if(search&&region){
  const cards=[...document.querySelectorAll('.card')];
  const update=()=>{const q=search.value.trim().toLocaleLowerCase();let count=0;for(const card of cards){const show=(region.value==='全部'||card.dataset.region===region.value)&&card.dataset.search.toLocaleLowerCase().includes(q);card.hidden=!show;if(show)count++;}document.querySelector('#result-count').textContent=`找到 ${count} 個景點`;document.querySelector('#empty').hidden=count!==0;};
  search.addEventListener('input',update);region.addEventListener('change',update);
  document.querySelector('#reset').addEventListener('click',()=>{search.value='';region.value='全部';update();search.focus();});update();
 }
 document.querySelectorAll('img').forEach(img=>img.addEventListener('error',()=>{img.alt='照片暫時無法顯示，請查看圖片出處連結';}));
})();
