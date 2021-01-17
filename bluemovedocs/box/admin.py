from django.contrib import admin
from .models import Box, Doc

@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'category',
        'title',
        'document_id',
        'examiner_email',
        'content',
        'content_update_flag',
        'image',
        'created_at',
        'deadline',
        'deadline_update_flag',
        'updated_at',
    )
    search_fields = (
        'category',
        'title',
        'document_id',
        'examiner_email',
        'content',
        'image',
        'deadline',
    )


@admin.register(Doc)
class DocAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'name',
        'file_id',
        'created_at',
        'submit_flag',
        'updated_at',
    )