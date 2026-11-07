(() => {
const root=document.getElementById('worker-skills-editor'); if(!root)return;
const catalog=JSON.parse(document.getElementById('worker-skill-catalog').textContent);
const hidden=root.querySelector('[name=specialties]');
let selected=[];try{const parsed=JSON.parse(hidden.value||'[]');if(Array.isArray(parsed))selected=parsed.filter(r=>r&&typeof r==='object'&&Number.isInteger(r.category)&&(r.tag===null||Number.isInteger(r.tag))&&typeof r.custom==='string');}catch(_){}
const picker=document.getElementById('skill-category-picker');
const suggestions=document.getElementById('suggested-specialties');
const groups=document.getElementById('selected-specialties');
const input=document.getElementById('custom-specialty');
const message=document.getElementById('skill-picker-message');
const text=(tag,value,cls)=>{const e=document.createElement(tag);e.textContent=value;if(cls)e.className=cls;return e;};
const getCategory=id=>catalog.find(c=>c.id===id);
const label=row=>row.tag?getCategory(row.category)?.tags.find(t=>t.id===row.tag)?.name||'Unavailable specialty':row.custom;
const normalize=s=>s.normalize('NFKC').trim().replace(/\s+/g,' ');
function render(){
 hidden.value=JSON.stringify(selected);
 groups.replaceChildren();
 const ids=[...new Set(selected.map(r=>r.category))];
 ids.forEach(id=>{const c=getCategory(id);const section=text('section','','selected-category');section.append(text('h3',c?.name||'Unavailable category'));const tags=text('div','','selected-skill-tags');selected.forEach((row,index)=>{if(row.category!==id)return;const chip=text('span','','selected-skill-chip');chip.append(text('span',label(row)));const remove=text('button','×');remove.type='button';remove.setAttribute('aria-label','Remove '+label(row));remove.addEventListener('click',()=>{selected.splice(index,1);render();});chip.append(remove);tags.append(chip);});section.append(tags);groups.append(section);});
 if(!selected.length)groups.append(text('p','Your selected specialties will appear here.','muted'));
 suggestions.replaceChildren();const category=getCategory(Number(picker.value));
 const disabled=!category||!category.active;input.disabled=disabled;document.getElementById('add-custom-specialty').disabled=disabled;
 if(category){suggestions.append(text('p','Suggested specialties','skill-suggestions-label'));const available=category.tags.filter(t=>t.active);available.forEach(tag=>{const chosen=selected.some(r=>r.tag===tag.id);const button=text('button',(chosen?'✓ ':'+ ')+tag.name,'skill-suggestion');button.type='button';button.setAttribute('aria-pressed',String(chosen));button.disabled=!category.active;button.addEventListener('click',()=>{if(chosen){selected=selected.filter(r=>r.tag!==tag.id);render();}else add({category:category.id,tag:tag.id,custom:''});});suggestions.append(button);});if(!available.length)suggestions.append(text('small','No suggested tags yet. Add a specialty below.'));}
}
function add(row){message.textContent='';if(selected.length>=30){message.textContent='Choose up to 30 specialties.';return;}if(!selected.some(r=>r.category===row.category)&&new Set(selected.map(r=>r.category)).size>=5){message.textContent='Choose up to 5 categories.';return;}const name=row.tag?getCategory(row.category).tags.find(t=>t.id===row.tag).name:row.custom;if(selected.some(r=>r.category===row.category&&label(r).toLocaleLowerCase()===name.toLocaleLowerCase())){message.textContent='That specialty is already selected.';return;}selected.push(row);render();}
catalog.forEach(c=>{const o=document.createElement('option');o.value=c.id;o.textContent=c.name;o.disabled=!c.active;picker.append(o);});
document.getElementById('skill-empty-catalog').hidden=catalog.some(c=>c.active);
picker.addEventListener('change',()=>{message.textContent='';render();});
function addCustom(){const category=getCategory(Number(picker.value));const custom=normalize(input.value);if(!category?.active||!custom){message.textContent='Select a category and enter a specialty.';return;}const tag=category.tags.find(t=>t.name.toLocaleLowerCase()===custom.toLocaleLowerCase());if(tag&&!tag.active){message.textContent='That suggested specialty is inactive.';return;}add({category:category.id,tag:tag?.id||null,custom:tag?'':custom});input.value='';input.focus();}
document.getElementById('add-custom-specialty').addEventListener('click',addCustom);
input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();addCustom();}});
render();
})();