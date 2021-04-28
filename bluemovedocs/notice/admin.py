from django.contrib import admin
from .models import *

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'category',
        'title',
        'old_title',
        'content',
        'image',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'category',
        'title',
        'content',
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'writer',
        'content',
    )