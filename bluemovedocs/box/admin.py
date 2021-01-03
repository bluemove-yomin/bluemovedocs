from django.contrib import admin
from .models import Box

@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'category',
        'title',
        'image',
        'created_at',
        'deadline',
        'updated_at',
    )
    search_fields = (
        'category',
        'title',
        'content',
    )