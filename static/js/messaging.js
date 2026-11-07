// Messenger interactions: conversation search, replies, emoji, and private updates.
(() => {
    const search = document.getElementById('thread-search');
    search?.addEventListener('input', () => {
        document.querySelectorAll('.messenger-thread').forEach(thread => {
            thread.hidden = !thread.textContent.toLowerCase().includes(search.value.toLowerCase());
        });
    });
    const list = document.getElementById('chat-message-list');
    if (!list) return;
    const compose = document.getElementById('chat-compose');
    const body = document.getElementById('id_body');
    const reply = document.getElementById('reply-composer');
    const replyId = document.getElementById('reply-to');
    list.scrollTop = list.scrollHeight;
    body.addEventListener('keydown', event => {
        if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
            event.preventDefault();
            if (body.value.trim() || document.getElementById('id_attachments').files.length) compose.requestSubmit();
        }
    });
    body.addEventListener('input', () => { body.style.height = 'auto'; body.style.height = Math.min(body.scrollHeight, 140) + 'px'; });
    list.addEventListener('click', event => {
        const button = event.target.closest('[data-reply-id]');
        if (!button) return;
        replyId.value = button.dataset.replyId;
        document.getElementById('reply-preview').textContent = button.dataset.replyText;
        reply.hidden = false;
        button.closest('details').open = false;
        body.focus();
    });
    document.getElementById('cancel-reply').addEventListener('click', () => { reply.hidden = true; replyId.value = ''; });
    const picker = document.getElementById('emoji-picker');
    const emojiToggle = document.querySelector('.emoji-toggle');
    emojiToggle.addEventListener('click', () => { picker.hidden = !picker.hidden; emojiToggle.setAttribute('aria-expanded', String(!picker.hidden)); });
    picker.addEventListener('click', event => {
        const button = event.target.closest('[data-insert-emoji]');
        if (!button) return;
        body.setRangeText(button.dataset.insertEmoji, body.selectionStart, body.selectionEnd, 'end');
        body.focus();
    });
    document.querySelector('.chat-info-toggle').addEventListener('click', event => {
        const panel = document.getElementById('chat-person-info');
        panel.hidden = !panel.hidden;
        event.currentTarget.setAttribute('aria-expanded', String(!panel.hidden));
    });
    const filesInput = document.getElementById('id_attachments');
    const filesList = document.getElementById('chat-selected-files');
    filesInput.addEventListener('change', () => {
        filesList.replaceChildren();
        const files = [...filesInput.files];
        files.forEach(file => { const label = document.createElement('span'); label.textContent = file.name; filesList.append(label); });
        if (files.length) { const clear = document.createElement('button'); clear.type = 'button'; clear.textContent = 'Remove files'; clear.addEventListener('click', () => {filesInput.value=''; filesList.replaceChildren();}); filesList.append(clear); }
    });
    const modal = document.getElementById('booking-modal');
    document.getElementById('open-booking')?.addEventListener('click', () => modal.showModal());
    document.querySelectorAll('[data-close-booking]').forEach(button => button.addEventListener('click', () => modal.close()));
    const openModal = document.getElementById('open-booking-modal');
    if (modal && openModal && JSON.parse(openModal.textContent)) modal.showModal();
    let fetching = false;
    let lastSignature = '';
    let lastBookingSignature = '';
    const timer = setInterval(async () => {
        if (fetching || document.hidden || list.querySelector('details[open]') || [...list.querySelectorAll('video')].some(v => !v.paused)) return;
        fetching = true;
        try {
            const response = await fetch(document.querySelector('[data-updates-url]').dataset.updatesUrl, {headers: {'Accept': 'application/json'}});
            if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) throw new Error('Unavailable');
            const data = await response.json();
            if (data.booking_signature !== lastBookingSignature && !document.querySelector('.booking-tickets details[open]')) {
                document.getElementById('booking-tickets').innerHTML = data.booking_html;
                lastBookingSignature = data.booking_signature;
            }
            const bottom = list.scrollHeight - list.scrollTop - list.clientHeight < 100;
            if (data.signature !== lastSignature) {
                const position = list.scrollTop;
                list.innerHTML = data.html;
                lastSignature = data.signature;
                list.scrollTop = bottom ? list.scrollHeight : position;
            }
            document.getElementById('chat-connection-status').hidden = true;
        } catch (_) {
            document.getElementById('chat-connection-status').hidden = false;
        } finally { fetching = false; }
    }, 4000);
    window.addEventListener('pagehide', () => clearInterval(timer));
})();
