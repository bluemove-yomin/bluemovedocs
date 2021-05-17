from django import forms
from .models import *
from ckeditor.widgets import CKEditorWidget

class BoxContentForm(forms.ModelForm):
    content = forms.CharField(widget = CKEditorWidget(), label='', required=True)
    class Meta:
        model = Box
        fields = [
            'content'
        ]


    def save(self, **kwargs):
        box = super().save(commit=False)
        box.writer = kwargs.get('writer', None)
        box.category = kwargs.get('category', None)
        box.prefix = kwargs.get('prefix', None)
        box.project_id = kwargs.get('project_id', None)
        box.project_name = kwargs.get('project_name', None)
        box.title = kwargs.get('title', None)
        box.drive_name = kwargs.get('drive_name', None)
        box.folder_name = kwargs.get('folder_name', None)
        box.folder_prefix = kwargs.get('folder_prefix', None)
        box.document_id = kwargs.get('document_id', None)
        box.document_name = kwargs.get('document_name', None)
        box.document_mimetype = kwargs.get('document_mimetype', None)
        box.folder_id = kwargs.get('folder_id', None)
        box.channel_id = kwargs.get('channel_id', None)
        box.channel_name = kwargs.get('channel_name', None)
        box.deadline = kwargs.get('deadline', None)
        box.image = kwargs.get('image', None)
        box.official_template_flag = kwargs.get('official_template_flag', None)
        box.save()
        return box


    def update(self, **kwargs):
        box = super().save(commit=False)
        box.prefix = kwargs.get('prefix', None)
        box.project_id = kwargs.get('project_id', None)
        box.project_name = kwargs.get('project_name', None)
        box.drive_name = kwargs.get('drive_name', None)
        box.folder_name = kwargs.get('folder_name', None)
        box.folder_prefix = kwargs.get('folder_prefix', None)
        box.folder_id = kwargs.get('folder_id', None)
        box.channel_id = kwargs.get('channel_id', None)
        box.channel_name = kwargs.get('channel_name', None)
        box.deadline = kwargs.get('deadline', None)
        box.save()
        return box