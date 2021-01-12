from django.contrib import admin
from .models import Box

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
    )
    search_fields = (
        'category',
        'title',
        'content',
    )