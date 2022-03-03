from django.core.exceptions import ValidationError


def file_size(file):
    limit = 26214400
    if file.size > limit:
        raise ValidationError('File too large. Size should not exceed 25 mb.')
