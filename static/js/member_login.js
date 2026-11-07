(() => {
const dialog = document.getElementById('member-login');
if (!dialog) return;
const open = () => { if (!dialog.open) dialog.showModal(); };
document.querySelectorAll('[data-login-trigger]').forEach(button => button.addEventListener('click', event => { event.preventDefault(); open(); }));
document.getElementById('close-login').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => { if (event.target === dialog) { const bounds=dialog.getBoundingClientRect(); if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close(); } });
const toggle = dialog.querySelector('[data-toggle-password]');
toggle.addEventListener('click', () => {const field=document.getElementById(toggle.getAttribute('aria-controls'));const visible=field.type==='password';field.type=visible?'text':'password';toggle.textContent=visible?'Hide':'Show';toggle.setAttribute('aria-pressed',String(visible));});
const state=document.getElementById('open-member-login');
if(state && JSON.parse(state.textContent)) open();
})();