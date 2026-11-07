// Preview the selected post photo without uploading it until Post update is pressed.
(() => {
    const input = document.querySelector('.post-photo-control input[type="file"]');
    if (!input) return;
    const preview = document.querySelector('.post-photo-preview');
    let imageUrl;
    function clearPreview() {
        if (imageUrl) URL.revokeObjectURL(imageUrl);
        imageUrl = undefined;
        preview.querySelector('img').removeAttribute('src');
        preview.hidden = true;
    }
    input.addEventListener('change', () => {
        clearPreview();
        const file = input.files[0];
        if (!file) return;
        if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) return;
        imageUrl = URL.createObjectURL(file);
        preview.querySelector('img').src = imageUrl;
        preview.hidden = false;
    });
    preview.querySelector('[data-remove-post-photo]').addEventListener('click', () => {
        input.value = '';
        clearPreview();
    });
    window.addEventListener('pagehide', clearPreview);
})();
