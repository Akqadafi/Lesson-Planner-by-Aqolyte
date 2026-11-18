const presets=JSON.parse(document.getElementById('preset-data').textContent);
const supplied=JSON.parse(document.getElementById('selected-data').textContent);
const setup=document.getElementById('setup');
function sync(initial=false){const mode=setup.elements.mode.value;const ids=initial&&supplied!==null?supplied:(mode==='scratch'?[]:presets[setup.elements.preset.value][1]);for(const box of setup.querySelectorAll('[name=sections]')){box.checked=ids.includes(box.value);box.disabled=mode==='preset';}}
setup.querySelectorAll('[name=mode],#preset').forEach(el=>el.addEventListener('change',()=>sync()));sync(true);
let dirty=false;const editor=document.getElementById('editor');if(editor)editor.addEventListener('input',()=>dirty=true);
document.querySelectorAll('form').forEach(form=>form.addEventListener('submit',event=>{if(dirty&&form!==editor){event.preventDefault();document.getElementById('progress').textContent='Save your section edits before using another control.';return;}const button=event.submitter;if(form===setup&&editor&&!confirm('Start a new lesson? This replaces the active working draft. Saved Library lessons remain available.')){event.preventDefault();return;}if(form===editor)dirty=false;const generation=form.classList.contains('generation')||button?.value==='regenerate'||button?.value==='create_generate';if(generation){document.getElementById('progress').textContent='Drafting your lesson. This may take a moment…';} }));
window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
