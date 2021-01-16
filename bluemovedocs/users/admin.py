from django.contrib import admin
from .models import *


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'level',
        'name_update_flag',
    )
    search_fields = (
        'user',
        'level',
    )