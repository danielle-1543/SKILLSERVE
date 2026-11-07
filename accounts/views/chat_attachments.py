"""Participant-only chat attachments with inline image/video previews."""
import mimetypes
import re
from pathlib import Path
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, StreamingHttpResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.clickjacking import xframe_options_sameorigin
from accounts.models import ChatAttachment
from .messaging import participant_thread


@xframe_options_sameorigin
@login_required(login_url='login')
def chat_attachment(request, pk):
    attachment = get_object_or_404(ChatAttachment.objects.select_related('message'), pk=pk, message__deleted_at__isnull=True)
    participant_thread(request.user, attachment.message.conversation_id)
    file = attachment.file.open('rb')
    size = attachment.file.size
    ext = Path(attachment.file.name).suffix.lower()
    mime = {'.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp','.mp4':'video/mp4','.webm':'video/webm','.pdf':'application/pdf','.txt':'text/plain; charset=utf-8'}.get(ext, mimetypes.guess_type(attachment.name)[0] or 'application/octet-stream')
    range_header = request.headers.get('Range', '')
    if attachment.kind == 'video' and range_header:
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', range_header)
        if not match or not any(match.groups()):
            file.close()
            return HttpResponse(status=416, headers={'Content-Range': f'bytes */{size}'})
        start = int(match[1]) if match[1] else max(0, size-int(match[2]))
        end = min(size-1, int(match[2])) if match[1] and match[2] else size-1
        if start >= size or start > end:
            file.close()
            return HttpResponse(status=416, headers={'Content-Range': f'bytes */{size}'})
        def chunks():
            try:
                file.seek(start)
                remaining = end-start+1
                while remaining:
                    chunk = file.read(min(65536, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk
            finally:
                file.close()
        response = StreamingHttpResponse(chunks(), status=206, content_type=mime)
        response['Content-Range'] = f'bytes {start}-{end}/{size}'
        response['Content-Length'] = end-start+1
    else:
        response = FileResponse(file, as_attachment=ext in {'.docx','.xlsx','.pptx'}, filename=attachment.name, content_type=mime)
    response['Accept-Ranges'] = 'bytes'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store'
    return response
