'use strict';
(() => {
  const byId=id=>document.getElementById(id);
  const sides=['before','after'], images={}, versions={before:0,after:0}, cursors={};
  let pairs=[],pending=null;
  const use=byId('use-picked-landmarks'),status=byId('picker-state');
  function fit(side){const image=images[side],canvas=byId('pick-'+side);if(!image)return null;const scale=Math.min(canvas.width/image.width,canvas.height/image.height);return {scale,x:(canvas.width-image.width*scale)/2,y:(canvas.height-image.height*scale)/2};}
  function paint(side){
    const canvas=byId('pick-'+side),ctx=canvas.getContext('2d'),image=images[side],f=fit(side);ctx.fillStyle='#17382c';ctx.fillRect(0,0,canvas.width,canvas.height);
    if(!image){ctx.fillStyle='#c5ddca';ctx.font='13px system-ui';ctx.fillText('Choose an image to prepare this view.',25,180);return;}
    ctx.drawImage(image,f.x,f.y,image.width*f.scale,image.height*f.scale);
    function marker(point,index,color){const x=f.x+point[0]*f.scale,y=f.y+point[1]*f.scale;ctx.strokeStyle=color;ctx.lineWidth=2;ctx.beginPath();ctx.arc(x,y,6,0,2*Math.PI);ctx.stroke();ctx.fillStyle=color;ctx.font='bold 13px system-ui';ctx.fillText(String(index),x+8,y-7);}
    pairs.forEach((row,i)=>marker(side==='before'?row.slice(2):row.slice(0,2),i+1,i>=pairs.length-2?'#ffc15c':'#43e1a8'));
    if(pending&&side==='before')marker(pending,pairs.length+1,'#ffffff');
    if(cursors[side]){const [px,py]=cursors[side],x=f.x+px*f.scale,y=f.y+py*f.scale;ctx.strokeStyle='#ffffff';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x-9,y);ctx.lineTo(x+9,y);ctx.moveTo(x,y-9);ctx.lineTo(x,y+9);ctx.stroke();}
  }
  function update(){
    const ready=images.before&&images.after;
    use.disabled=!ready||pairs.length<6||pending!==null;
    if(use.disabled)use.checked=false;
    document.querySelector('textarea[name=landmarks]').disabled=use.checked;
    status.textContent=!ready?'Choose both images. Previews use the same processing as the analysis.':pending?`Pair ${pairs.length+1}: select its match in AFTER.`:`${pairs.length} complete pairs. ${pairs.length>=6?'Ready; final two pairs are held out. Enable “Use picked landmarks” to apply.':'Add '+(6-pairs.length)+' more pairs.'} Next select BEFORE.`;
    sides.forEach(paint);
  }
  function clear(){pairs=[];pending=null;use.checked=false;update();}
  async function prepare(side){
    const version=++versions[side],file=byId(side).files[0];
    if(images[side])images[side].close();delete images[side];clear();
    if(!file)return;
    status.textContent='Preparing processed image preview…';
    const data=new FormData();data.set('image',file);
    try{
      const response=await fetch('/api/preview',{method:'POST',body:data});
      if(!response.ok){const error=await response.json();throw new Error(error.detail||'Could not prepare image.');}
      const image=await createImageBitmap(await response.blob());
      if(version!==versions[side]){image.close();return;}
      images[side]=image;cursors[side]=[Math.floor(image.width/2),Math.floor(image.height/2)];update();
    }catch(error){if(version===versions[side])status.textContent=error.message;}
  }
  function select(side,point){
    if(!images.before||!images.after)return;
    if((side==='before'&&pending)||(side==='after'&&!pending)){status.textContent=pending?'Select the matching point in AFTER.':'Select a point in BEFORE first.';return;}
    if(pairs.length>=20){status.textContent='Maximum 20 pairs. Undo or clear picks to change them.';return;}
    if(side==='before')pending=[...point];
    else{pairs.push([...point,...pending]);pending=null;}
    update();
  }
  for(const side of sides){
    const canvas=byId('pick-'+side);
    canvas.onclick=event=>{const f=fit(side);if(!f)return;const bounds=canvas.getBoundingClientRect();const x=((event.clientX-bounds.left)*canvas.width/bounds.width-f.x)/f.scale,y=((event.clientY-bounds.top)*canvas.height/bounds.height-f.y)/f.scale;
      if(x<0||y<0||x>=images[side].width||y>=images[side].height)return;
      const point=[Math.min(images[side].width-1,Math.round(x*100)/100),Math.min(images[side].height-1,Math.round(y*100)/100)];cursors[side]=point;select(side,point);
    };
    canvas.onkeydown=event=>{if(!images[side])return;const point=cursors[side],step=event.shiftKey?10:1;
      if(event.key==='Enter'){event.preventDefault();select(side,[...point]);return;}
      const moves={ArrowLeft:[-step,0],ArrowRight:[step,0],ArrowUp:[0,-step],ArrowDown:[0,step]};
      if(moves[event.key]){event.preventDefault();const [dx,dy]=moves[event.key];point[0]=Math.max(0,Math.min(images[side].width-1,point[0]+dx));point[1]=Math.max(0,Math.min(images[side].height-1,point[1]+dy));paint(side);}
    };
    byId(side).addEventListener('change',()=>{clear();versions[side]++;if(byId('landmark-picker').open)prepare(side);else{if(images[side])images[side].close();delete images[side];}});
  }
  byId('landmark-picker').ontoggle=()=>{if(byId('landmark-picker').open)for(const side of sides)if(!images[side])prepare(side);};
  byId('undo-landmark').onclick=()=>{if(pending)pending=null;else pairs.pop();update();};
  byId('clear-landmarks').onclick=clear;
  async function imageIdentity(){
    const result={};
    for(const side of sides){
      const file=byId(side).files[0];
      if(!file||!images[side])throw new Error('Prepare both image previews first.');
      const digest=await crypto.subtle.digest('SHA-256',await file.arrayBuffer());
      result[side]={sha256:Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join(''),width:images[side].width,height:images[side].height};
    }
    return result;
  }
  const revision=()=>JSON.stringify([versions,pairs,pending]);
  byId('save-landmark-draft').onclick=async()=>{
    const initial=revision();
    try{
      if(pending)throw new Error('Complete or undo the pending pair before saving.');
      const identity=await imageIdentity();
      if(initial!==revision())throw new Error('Images or picks changed; save again.');
      const draft={schema:'geoalibi-landmark-draft-v1',coordinate_space:'processed-original-images',images:identity,landmarks:pairs,
        notice:'Unreviewed working draft. Image hashes bind coordinates to file bytes; they do not authenticate correspondences. Final two points are held out when applied.'};
      const url=URL.createObjectURL(new Blob([JSON.stringify(draft,null,2)],{type:'application/json'}));
      const link=document.createElement('a');link.href=url;link.download='geoalibi-landmark-draft.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
      status.textContent='Draft saved. Keep the original images for independent review.';
    }catch(error){status.textContent=error.message;}
  };
  byId('restore-landmark-draft').onchange=async event=>{
    const file=event.target.files[0],initial=revision();event.target.value='';
    if(!file)return;
    try{
      if(file.size>65536)throw new Error('Landmark draft exceeds 64 KB.');
      const draft=JSON.parse(await file.text()),identity=await imageIdentity();
      if(initial!==revision())throw new Error('Images or picks changed; restore again.');
      if(draft.schema!=='geoalibi-landmark-draft-v1'||draft.coordinate_space!=='processed-original-images')throw new Error('Unsupported landmark draft format.');
      for(const side of sides)for(const key of ['sha256','width','height'])if(draft.images?.[side]?.[key]!==identity[side][key])throw new Error('Draft does not match these original images and processed dimensions.');
      if(!Array.isArray(draft.landmarks)||draft.landmarks.length>20||draft.landmarks.some(row=>!Array.isArray(row)||row.length!==4||row.some((v,i)=>typeof v!=='number'||!Number.isFinite(v)||v<0||v>=identity[i<2?'after':'before'][i%2?'height':'width'])))throw new Error('Draft contains invalid landmark coordinates.');
      pairs=draft.landmarks.map(row=>[...row]);pending=null;use.checked=false;update();
      status.textContent=`Restored ${pairs.length} pairs. Review each correspondence; explicitly enable Use picked landmarks to apply.`;
    }catch(error){status.textContent=error.message;}
  };
  use.onchange=update;
  // Add picked points to this form's request only after explicit opt-in.
  byId('upload-form').addEventListener('formdata',event=>{if(use.checked)event.formData.set('landmarks',JSON.stringify(pairs));});
  update();
})();

