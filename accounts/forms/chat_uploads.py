"""Private chat upload validation and multiple-file form support."""
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from django import forms


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        if len(files) > 5:
            raise forms.ValidationError('Attach up to 5 files per message.')
        result = [super(MultipleFileField, self).clean(file, initial) for file in files]
        if sum(file.size for file in result) > 50 * 1024 * 1024:
            raise forms.ValidationError('The combined attachments must be 50 MB or less.')
        for file in result:
            validate_attachment(file)
        return result


def attachment_kind(filename):
    extension = Path(filename).suffix.lower()
    if extension in {'.jpg', '.jpeg', '.png', '.webp'}:
        return 'image'
    if extension in {'.mp4', '.webm'}:
        return 'video'
    return 'document'


def validate_attachment(file):
    if file.size > 25 * 1024 * 1024:
        raise forms.ValidationError('Each file must be 25 MB or less.')
    ext = Path(file.name).suffix.lower()
    head = file.read(64)
    file.seek(0)
    valid = False
    try:
        if ext in {'.jpg', '.jpeg', '.png', '.webp'}:
            from PIL import Image
            image = Image.open(file)
            expected = {'.jpg':'JPEG', '.jpeg':'JPEG', '.png':'PNG', '.webp':'WEBP'}[ext]
            valid = image.format == expected
            image.verify()
        elif ext == '.pdf':
            valid = head.startswith(b'%PDF-')
        elif ext == '.mp4':
            valid = head[4:8] == b'ftyp'
        elif ext == '.webm':
            valid = head.startswith(b'\x1a\x45\xdf\xa3')
        elif ext == '.txt':
            file.read().decode('utf-8')
            valid = True
        elif ext in {'.docx', '.xlsx', '.pptx'}:
            required = {'.docx':'word/document.xml', '.xlsx':'xl/workbook.xml', '.pptx':'ppt/presentation.xml'}[ext]
            with ZipFile(file) as archive:
                valid = required in archive.namelist() and '[Content_Types].xml' in archive.namelist()
    except (ValueError, OSError, UnicodeError, BadZipFile):
        valid = False
    finally:
        file.seek(0)
    if not valid:
        raise forms.ValidationError('Use a valid JPG, PNG, WebP, MP4, WebM, PDF, TXT, DOCX, XLSX, or PPTX file.')
