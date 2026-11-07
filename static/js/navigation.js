(() => {
 const toggle = document.querySelector('.ss-menu-toggle');
 if (!toggle) return;
 const mobile = window.matchMedia('(max-width: 900px)');
 let saved = false;
 try { saved = localStorage.getItem('skillserve-sidebar-hidden') === 'true'; } catch (_) {}
 const setHidden = (hidden) => {
  document.body.classList.toggle('ss-nav-hidden', hidden);
  toggle.setAttribute('aria-expanded', String(!hidden));
  toggle.setAttribute('aria-label', hidden ? 'Show navigation' : 'Hide navigation');
  const sidebar = document.getElementById('ss-navigation');
  sidebar.inert = hidden;
 };
 setHidden(mobile.matches || saved);
 toggle.addEventListener('click', () => {
  const hidden = !document.body.classList.contains('ss-nav-hidden');
  setHidden(hidden);
  if (!mobile.matches) { try { localStorage.setItem('skillserve-sidebar-hidden', String(hidden)); } catch (_) {} }
 });
 document.querySelector('.ss-scrim').addEventListener('click', () => setHidden(true));
 document.addEventListener('keydown', e => { if (e.key === 'Escape') { setHidden(true); toggle.focus(); } });
 mobile.addEventListener('change', () => setHidden(mobile.matches));
 const current = location.pathname;
 document.querySelectorAll('.ss-sidebar nav a').forEach(a => {
  if (a.pathname === current || (a.pathname === '/client/profile/' && current === '/saved-workers/') || (a.pathname === '/worker/profile/' && current === '/worker/profile/edit/') || (a.pathname === '/' && current.startsWith('/announcements/')) || (a.pathname === '/jobs/' && current.startsWith('/jobs/')) || (a.pathname === '/messages/' && current.startsWith('/messages/'))) a.setAttribute('aria-current', 'page');
 });
})();