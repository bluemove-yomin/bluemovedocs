from django.contrib import admin
from .models import *

@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'category',
        'title',
        'document_id',
        'content',
        'content_update_flag',
        'image',
        'created_at',
        'deadline',
        'deadline_update_flag',
        'updated_at',
        'official_template_flag',
    )
    search_fields = (
        'category',
        'title',
        'document_id',
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
        'outside_permission_id',
        'permission_id',
        'inside_permission_id',
        'created_at',
        'updated_at',
        'submit_flag',
        'reject_flag',
        'return_flag',
    )