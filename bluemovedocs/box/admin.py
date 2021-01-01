from django.contrib import admin
from .models import Box

@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'category',
        'title',
        'image',
        'deadline',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'category',
        'title',
        'content',
    )