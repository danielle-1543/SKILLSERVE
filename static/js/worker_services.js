(() => {
 const picker=document.querySelector('.service-types-editor'), section=document.querySelector('[data-prefix="services"]');
 if(!picker||!section)return;
 const checks=[...picker.querySelectorAll('input[type="checkbox"]')],holder=section.querySelector('.formset-rows'),cards=section.querySelector('.offered-service-cards'),message=section.querySelector('.offered-service-message'),total=section.querySelector('[name$="-TOTAL_FORMS"]');
 const max=Number(section.querySelector('[name$="-MAX_NUM_FORMS"]').value),drafts=new Map();
 const field=(row,key)=>row.querySelector(`[name$="-${key}"]`);
 const allRows=()=>[...section.querySelectorAll('.formset-row')];
 const active=()=>allRows().filter(r=>!field(r,'DELETE').checked&&(field(r,'name').value.trim()||field(r,'id').value));
 function el(parent,tag,text,cls){const n=document.createElement(tag);n.textContent=text||'';if(cls)n.className=cls;parent.append(n);return n;}
 function btn(parent,text,action){const n=el(parent,'button',text);n.type='button';n.onclick=action;return n;}
 function editor(parent,row){
  row.hidden=false;parent.append(row);row.querySelectorAll('.capsule-done').forEach(n=>n.remove());
  btn(row,'Done',()=>{if(!field(row,'name').value.trim()||field(row,'starting_rate').value===''||!field(row,'starting_rate').checkValidity()||!field(row,'service_type').value){message.textContent='Choose a type and enter a service with a valid rate.';return;}draw();}).className='capsule-done';
 }
 function draw(){
  allRows().forEach(r=>holder.append(r));
  const selected=checks.filter(c=>c.checked);
  document.getElementById('service-type-count').textContent=`${selected.length} / 5 types selected`;
  checks.forEach(c=>c.disabled=!c.checked&&selected.length>=5);
  allRows().forEach(row=>{const s=field(row,'service_type'),v=s.value;s.replaceChildren(new Option('Choose a service type',''),...selected.map(c=>new Option(c.closest('label').textContent.trim(),c.value)));s.value=selected.some(c=>c.value===v)?v:'';row.hidden=true;});
  cards.replaceChildren();
  message.textContent=selected.length?'Add your services below. Each added service becomes a capsule tag.':'Check a Type of Service above to get started.';
  selected.forEach(c=>{
   const card=el(cards,'section','','offered-type-card');el(card,'h3',c.closest('label').textContent.trim());
   const pills=el(card,'div','','offered-capsules');const matches=active().filter(r=>field(r,'service_type').value===c.value);
   if(!matches.length)el(pills,'p','No services added yet.','job-meta');
   matches.forEach(row=>{const pill=el(pills,'div','','offered-capsule');el(pill,'span',`${field(row,'name').value} · PHP ${field(row,'starting_rate').value}`);
    btn(pill,'Edit',()=>editor(card,row));const remove=btn(pill,'×',()=>{field(row,'DELETE').checked=true;draw();});remove.setAttribute('aria-label','Remove '+field(row,'name').value);
    if(row.querySelector('.errorlist'))editor(card,row);
   });
   const box=el(card,'div','','offered-entry');const d=drafts.get(c.value)||{name:'',rate:''};
   const nl=el(box,'label','Service Offered'),name=el(nl,'input');name.type='text';name.maxLength=160;name.placeholder='Describe what you can do';name.value=d.name;
   const rl=el(box,'label','Starting rate (PHP)'),rate=el(rl,'input');rate.type='number';rate.min='0';rate.max='99999999.99';rate.step='0.01';rate.placeholder='500';rate.value=d.rate;
   const remember=()=>{name.setCustomValidity('');rate.setCustomValidity('');drafts.set(c.value,{name:name.value,rate:rate.value});};name.oninput=remember;rate.oninput=remember;
   function add(){
    name.setCustomValidity(name.value.trim()?'':'Enter the service you offer.');rate.setCustomValidity(rate.value!==''?'':'Enter a starting rate.');
    if(!name.reportValidity()||!rate.reportValidity())return;
    if(active().length>=max){message.textContent=`Up to ${max} services are allowed.`;return;}
    const key=name.value.trim().replace(/\s+/g,' ').toLowerCase();
    if(active().some(r=>field(r,'service_type').value===c.value&&field(r,'name').value.trim().replace(/\s+/g,' ').toLowerCase()===key)){message.textContent='That service is already listed for this type.';return;}
    let row=allRows().find(r=>!field(r,'id').value&&(!field(r,'name').value.trim()||field(r,'DELETE').checked));
    if(!row){const i=Number(total.value);if(i>=1000){message.textContent='Save and reload before adding more.';return;}const t=document.createElement('template');t.innerHTML=section.querySelector('template.empty-form').innerHTML.replaceAll('__prefix__',i);row=t.content.firstElementChild;holder.append(row);total.value=i+1;}
    const type=field(row,'service_type');type.replaceChildren(new Option(c.closest('label').textContent.trim(),c.value));type.value=c.value;
    field(row,'name').value=name.value.trim();field(row,'starting_rate').value=rate.value;field(row,'DELETE').checked=false;
    drafts.delete(c.value);draw();
   }
   btn(box,'+ Add service',add).className='add-row-button';name.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();add();}};
   el(card,'p','Include per hour, per visit, or per job in the service name.','job-meta');
  });
  const orphaned=active().filter(r=>!field(r,'service_type').value);
  if(orphaned.length){const area=el(cards,'div','','offered-unlinked');el(area,'h3','Assign a type to these existing services');el(area,'p','Nothing was deleted. Choose a checked type or remove the entry.');orphaned.forEach(r=>editor(area,r));}
 }
 section.querySelector(':scope > .add-row-button').hidden=true;
 picker.addEventListener('change',draw);
 section.addEventListener('click',e=>{const b=e.target.closest('.remove-row-button');if(b){field(b.closest('.formset-row'),'DELETE').checked=true;draw();}});
 document.getElementById('service-type-filter').oninput=e=>{const q=e.target.value.trim().toLowerCase();checks.forEach(c=>{const row=c.closest('label').parentElement;row.hidden=!c.checked&&!row.textContent.toLowerCase().includes(q);});};
 picker.closest('form').addEventListener('submit',e=>{
  const selected=new Set(checks.filter(c=>c.checked).map(c=>c.value));
  const pending=[...drafts.entries()].some(([id,d])=>selected.has(id)&&(d.name.trim()||d.rate));
  if(pending){e.preventDefault();message.textContent='Click Add service for your typed entry before submitting.';message.scrollIntoView({block:'center'});return;}
  if(active().some(r=>!field(r,'service_type').value)){e.preventDefault();message.textContent='Choose a type for each existing service before submitting.';message.scrollIntoView({block:'center'});}
 });
 draw();
})();
