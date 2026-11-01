'use strict';
const $ = id => document.getElementById(id);
let report = null, selected = null, scenario = 'mixed', filter = 'all', view = 'swipe', busy = false;
const verdictNames = {supported:'SUPPORTED',artifact:'NUISANCE EXPLAINED',review:'REVIEW NEEDED'};
const element = (tag, className, text) => { const e = document.createElement(tag); if(className)e.className=className; if(text!==undefined)e.textContent=text; return e; };
async function api(path, options={}) {
  const response = await fetch(path, options);
  const data = await response.json();
  if(!response.ok) throw new Error(typeof data.detail==='string'?data.detail:'Check the image files and analysis settings.');
  return data;
}
function showError(error) { $('error').textContent=error.message; $('error').hidden=false; }
function settings(){
  const threshold=Number($('threshold').value), min_area=Number($('min-area').value);
  if(!Number.isFinite(threshold)||threshold<.04||threshold>.4||!Number.isInteger(min_area)||min_area<16||min_area>10000)throw new Error('Threshold must be 0.04–0.40; minimum area must be 16–10000 pixels.');
  return {threshold,min_area,detector:$('detector').value,use_meta:$('use-meta').checked,use_sam:$('use-sam').checked};
}
async function status(){
  const s=await api('/api/status');
  $('use-meta').disabled=!s.meta_configured;
  document.querySelector('#detector option[value=unet]').disabled=!s.detector_configured;
  $('meta-state').textContent=s.meta_configured?'Key configured · optional paid calls':'API key not configured · local checks available';
  $('use-sam').disabled=!s.sam_configured||!$('use-meta').checked;
  $('budget-text').textContent=`$${s.budget.reserved_usd.toFixed(2)} reserved against a $${s.budget.ceiling_usd.toFixed(2)} local ceiling. Each uncached interpretation reserves $0.50 conservatively, including failed calls. This is not measured spending; verify actual charges and remaining credits in Meta Billing.`;
  return s;
}
async function history(){
  const runs=await api('/api/runs'); $('history').replaceChildren();
  if(!runs.length)$('history').append(element('span','muted','No investigations yet.'));
  for(const run of runs){const b=element('button','',run.title);b.append(element('small','',new Date(run.created).toLocaleString()));b.onclick=async()=>{if(busy)return;try{render(await api('/api/runs/'+run.id));}catch(e){showError(e);}};$('history').append(b);}
}
function setBusy(value){busy=value;$('loading').hidden=!value;$('run').disabled=value;document.querySelector('#upload-form button').disabled=value;$('export').disabled=value||!report;$('packet').disabled=value||!report;}
async function investigate(path, options){
  if(busy)return;setBusy(true);$('error').hidden=true;$('empty').hidden=true;
  try{render(await api(path,options));await history();await status();}
  catch(error){showError(error);if(!report)$('empty').hidden=false;}
  finally{setBusy(false);}
}
function render(data){
  report=data;selected=data.regions[0]?.id??null;filter='all';
  $('results').hidden=false;$('empty').hidden=true;$('method').hidden=true;
  $('count-total').textContent=data.regions.length;$('count-supported').textContent=data.counts.supported;
  $('count-artifact').textContent=data.counts.artifact;$('count-review').textContent=data.counts.review;
  $('run-title').textContent=data.title;$('fixture-badge').hidden=!data.synthetic;
  $('elapsed').textContent=`${(data.elapsed_ms/1000).toFixed(2)}s · ${data.detector}`;
  $('dimensions').textContent=`${data.width} × ${data.height} px`;
  renderAssessment(data);
  $('alignment-label').textContent=`${data.alignment.method} · ${(data.alignment.overlap*100).toFixed(1)}% overlap`;
  $('warnings').replaceChildren(...data.warnings.map(w=>element('p','',w)));
  $('compare-image').src=data.assets.aligned;
  setView(view);renderRegions();renderDetail();renderModel();$('export').disabled=false;$('packet').disabled=false;
  document.querySelectorAll('.filter').forEach(b=>b.classList.toggle('active',b.dataset.filter===filter));
}
function renderAssessment(data){
  const a=data.assessment;
  $('assessment-title').textContent=a?.title||'Inspection scope was not recorded';
  $('assessment-panel').dataset.state=a?.code||'legacy';
  $('assessment-detail').textContent=a?.detail||'This saved investigation has no current scope summary. Its original verdicts are preserved.';
  $('inspect-omitted').hidden=!a?.omitted_regions||!data.assets.omitted_overlay;
  for(const name of ['omitted_overlay','omitted_mask'])document.querySelector(`[data-view="${name}"]`).disabled=!data.assets[name];
  const c=a?.coverage;
  $('assessment-coverage').textContent=a?`${a.inspected_regions} / ${a.eligible_regions} eligible regions inspected · ${a.omitted_regions} omitted · ${a.supported_pixels.toLocaleString()} supported pixels`+(c?` · ${c.omitted_region_pixels.toLocaleString()} eligible-region pixels omitted`:' · detailed pixel coverage unavailable for this older run'):'';
  $('assessment-next').textContent=a?.next_step||'Review the recorded warnings and acquisition context.';
}
$('inspect-proposals').onclick=()=>setView('proposal_mask');
$('inspect-omitted').onclick=()=>setView('omitted_overlay');
function setView(name){
  if(!report)return;
  if(name!=='swipe'&&!report.assets[name])name='swipe';
  view=name;
  $('omission-note').hidden=!['omitted_overlay','omitted_mask'].includes(name);
  document.querySelectorAll('.tab').forEach(b=>{b.classList.toggle('active',b.dataset.view===name);b.setAttribute('aria-pressed',String(b.dataset.view===name));});
  const compare=name==='swipe';
  $('base-image').src=report.assets[compare?'before':name];$('base-image').alt=compare?'Before image':name+' image';
  for(const id of ['compare-layer','swipe-line','scrubber','before-label','after-label'])$(id).hidden=!compare;
  drawRegion();
}
function renderRegions(){
  const list=report.regions.filter(r=>filter==='all'||r.verdict===filter);$('regions').replaceChildren();
  if(!list.length){$('regions').append(element('p','muted',report.regions.length?'No regions in this filter.':'No candidate exceeds the current thresholds. Lower the threshold or inspect the pair manually.'));return;}
  for(const region of list){
    const b=element('button','region'+(region.id===selected?' selected':''));b.setAttribute('aria-label',region.id+' '+region.title);b.setAttribute('aria-pressed',String(region.id===selected));
    const top=element('div','region-top');top.append(element('span','region-id',region.id),element('span','verdict '+region.verdict,verdictNames[region.verdict]));
    const bottom=element('div','region-bottom');bottom.append(element('span','',region.pixels.toLocaleString()+' px'),element('span','',region.review.replaceAll('_',' ')));
    b.append(top,element('h3','',region.title),element('p','',region.contradictions[0]||region.support[0]||'Inspect the source pixels.'),bottom);
    b.onclick=()=>{if(['omitted_overlay','omitted_mask'].includes(view))setView('overlay');selected=region.id;renderRegions();renderDetail();drawRegion();};$('regions').append(b);
  }
}
function drawRegion(){
  const c=$('region-canvas');if(!report)return;
  const bounds=$('viewer').getBoundingClientRect();const ratio=window.devicePixelRatio||1;c.width=Math.round(bounds.width*ratio);c.height=Math.round(bounds.height*ratio);
  if(['omitted_overlay','omitted_mask'].includes(view))return;
  const ctx=c.getContext('2d');ctx.scale(ratio,ratio);const region=report.regions.find(r=>r.id===selected);if(!region)return;
  const scale=Math.min(bounds.width/report.width,bounds.height/report.height),ox=(bounds.width-report.width*scale)/2,oy=(bounds.height-report.height*scale)/2;
  const [x,y,w,h]=region.bbox;ctx.strokeStyle=region.verdict==='supported'?'#43e1a8':region.verdict==='review'?'#ffc15c':'#9ab8de';ctx.lineWidth=2;ctx.setLineDash([5,4]);ctx.strokeRect(ox+x*scale,oy+y*scale,w*scale,h*scale);
}
function evidenceColumn(title,items,cls){const div=element('div',cls);div.append(element('h3','',title));const ul=element('ul');for(const text of items.length?items:['No decisive evidence recorded.'])ul.append(element('li','',text));div.append(ul);return div;}
function renderDetail(){
  const r=report.regions.find(x=>x.id===selected);$('detail-body').replaceChildren();
  if(!r){$('detail-title').textContent='No candidate to inspect.';return;}
  $('detail-title').textContent=r.id+' / '+r.title;
  const checks=element('div','checks');
  const names={alignment_reduction:'Registration reduction',lighting_reduction:'Illumination reduction',retained_fraction:'Pixels retained',structural_disagreement:'Edge disagreement',perturbation_survival:'Perturbation survival',local_luminance_correlation:'Luminance correlation'};
  for(const [key,name] of Object.entries(names)){const card=element('div','check');card.append(element('span','',name),element('strong','',Math.round(r.checks[key]*100)+'%'));checks.append(card);}
  const cols=element('div','evidence-columns');cols.append(evidenceColumn('↗ SUPPORTING EVIDENCE',r.support,''),evidenceColumn('⊖ CONTRADICTORY EVIDENCE',r.contradictions,'contradict'));
  const form=element('form','review-form'),select=element('select');select.setAttribute('aria-label','Human review decision');
  for(const [value,text] of Object.entries({unreviewed:'Unreviewed',confirmed:'Confirmed by reviewer',dismissed:'Dismissed by reviewer',needs_field_check:'Needs independent evidence'})){const o=element('option','',text);o.value=value;select.append(o);}select.value=r.review;
  const note=element('input');note.placeholder='Record evidence or a reason for your decision';note.maxLength=1000;note.value=r.review_note||'';note.setAttribute('aria-label','Review evidence note');
  const save=element('button','primary','Save review');save.type='submit';form.append(select,note,save);
  const saved=element('p','review-note',`${report.audit?.length||0} review entries in this investigation · Automated verdicts are preserved.`);saved.setAttribute('role','status');
  form.onsubmit=async event=>{event.preventDefault();save.disabled=true;try{report=await api(`/api/runs/${report.id}/reviews/${r.id}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({decision:select.value,note:note.value})});renderRegions();renderDetail();}catch(e){showError(e);}finally{save.disabled=false;}};
  const dossier=element('div','dossier');dossier.append(element('h3','','Alternative explanations: challenge log'));
  for(const item of r.challenge_log||[]){const row=element('article','challenge');const labels={persists:'DIFFERENCE REMAINS',explained:'DIFFERENCE REDUCED',plausible:'STILL PLAUSIBLE',unresolved:'NEEDS EVIDENCE',untested:'NOT TESTED',sensitive:'SHIFT SENSITIVE'};const titles={registration:'Alignment correction',illumination:'Global lighting correction',local_appearance:'Local appearance check',registration_stress:'One-pixel registration stress',season_cloud_sensor:'Other explanations'};row.append(element('span','model-status',labels[item.result]||item.result.toUpperCase()),element('strong','',titles[item.id]||'Alternative explanation'),element('p','','Alternative: '+item.hypothesis),element('p','',item.scope));
    for(const experiment of item.experiments||[])row.append(element('span','model-status',`Shift (${experiment.dx}, ${experiment.dy}): ${Math.round(experiment.survival*100)}% retained`));dossier.append(row);}
  dossier.append(element('h3','','What evidence would help next?'));
  for(const [index,request] of (r.evidence_requests||[]).entries()){
    const card=element('article','challenge');card.append(element('p','',`${request.priority}. ${request.request}`));
    const history=(report.evidence_audit||[]).filter(e=>e.region_id===r.id&&e.request_index===index);
    card.append(element('p','',history.length?'Latest response: '+history.at(-1).status:'Awaiting independent evidence'));
    for(const entry of history)card.append(element('p','',`${entry.created} · ${entry.status} · ${entry.source||'No source'} · ${entry.note}`));
    const ef=element('form','review-form'),status=element('select');status.setAttribute('aria-label','Evidence response status');
    for(const [value,label] of Object.entries({provided:'Evidence supplied',unavailable:'Cannot obtain evidence',retracted:'Retract earlier evidence'})){const o=element('option','',label);o.value=value;status.append(o);}
    const source=element('input');source.placeholder='Source reference, acquisition ID or field report';source.maxLength=500;source.setAttribute('aria-label','Evidence source reference');
    const enote=element('input');enote.placeholder='Observation and limitations';enote.maxLength=1500;enote.required=true;enote.setAttribute('aria-label','Evidence observation');
    const submit=element('button','primary','Record evidence response');submit.type='submit';ef.append(status,source,enote,submit);
    ef.onsubmit=async event=>{event.preventDefault();submit.disabled=true;try{report=await api(`/api/runs/${report.id}/evidence/${r.id}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({request_index:index,status:status.value,source:source.value,note:enote.value})});renderDetail();}catch(e){showError(e);}finally{submit.disabled=false;}};
    card.append(ef);dossier.append(card);
  }
  dossier.append(element('p','evidence-note','Evidence responses are reviewer statements, not authenticated sources. Recording or retracting evidence does not change automated verdicts.'));
  $('detail-body').append(checks,cols,dossier,form,saved);
}
function renderModel(){
  const out=$('model-output');out.replaceChildren();
  out.append(element('span','model-status','MUSE · '+report.meta.status.toUpperCase()),element('span','model-status','SAM · '+report.sam.status.toUpperCase()));
  if(report.meta.status==='completed'){
    out.append(element('p','',report.meta.interpretation.summary));
    for(const r of report.meta.interpretation.regions){out.append(element('h3','',r.id+' · '+r.hypothesis));out.append(evidenceColumn('Alternative explanations',r.alternate_explanations,''),evidenceColumn('Evidence still needed',r.needed_evidence,''));}
    out.append(element('p','',report.meta.note+(report.meta.cache_hit?' · Cached response; no new interpretation request.':'')));
  }else out.append(element('p','',report.meta.reason||'No model interpretation requested. Configure MODEL_API_KEY on the server and enable interpretation before running an investigation.'));
  if(report.sam.status==='completed'){
    out.append(element('p','',`SAM 3.1 found ${report.sam.before.objects.length} building objects before and ${report.sam.after.objects.length} after. These counts alone are not proof of change.`));
    for(const r of report.sam.regions)out.append(element('p','',`${r.id}: building coverage ${(r.building_fraction_before*100).toFixed(1)}% before → ${(r.building_fraction_after*100).toFixed(1)}% after.`));
    for(const [name,text] of [['sam_before_mask','View before building mask'],['sam_after_mask','View after building mask']]){
      if(report.assets[name]){const a=element('a','model-status',text);a.href=report.assets[name];a.target='_blank';a.rel='noopener';out.append(a);}
    }
  }else if(report.sam.reason)out.append(element('p','',report.sam.reason));
}
document.querySelectorAll('.case').forEach(b=>b.onclick=()=>{scenario=b.dataset.case;document.querySelectorAll('.case').forEach(x=>x.classList.toggle('active',x===b));});
$('run').onclick=()=>{try{investigate('/api/demo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({case:scenario,...settings()})});}catch(e){showError(e);}};
$('toggle-upload').onclick=()=>{$('upload-form').hidden=!$('upload-form').hidden;};
$('upload-form').onsubmit=event=>{event.preventDefault();try{const data=new FormData(event.target);for(const [k,v]of Object.entries(settings()))data.set(k,String(v));investigate('/api/analyze',{method:'POST',body:data});}catch(e){showError(e);}};
$('use-meta').onchange=()=>{status().catch(showError);if(!$('use-meta').checked)$('use-sam').checked=false;};
$('swipe').oninput=()=>{const value=$('swipe').value;$('compare-layer').style.clipPath=`inset(0 0 0 ${value}%)`;$('swipe-line').style.left=value+'%';};
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>setView(b.dataset.view));
document.querySelectorAll('.filter').forEach(b=>b.onclick=()=>{filter=b.dataset.filter;document.querySelectorAll('.filter').forEach(x=>x.classList.toggle('active',x===b));renderRegions();});
$('export').onclick=()=>{if(report)window.location.href=`/api/runs/${report.id}/report`;};
$('nav-method').onclick=()=>{$('method').hidden=!$('method').hidden;if(!$('method').hidden)$('method').scrollIntoView({behavior:'smooth'});};
$('nav-work').onclick=()=>{window.scrollTo({top:0,behavior:'smooth'});};
window.addEventListener('resize',drawRegion);
Promise.all([status(),history()]).catch(showError);

$('packet').onclick=()=>{if(report)window.location.href=`/api/runs/${report.id}/packet`;};

