from django import forms
from .models import *
from ckeditor.widgets import CKEditorWidget

class NoticeContentForm(forms.ModelForm):
    content = forms.CharField(widget = CKEditorWidget(), label='', required=True)
    class Meta:
        model = Notice
        fields = [
            'content'
        ]


    def save(self, **kwargs):
        notice = super().save(commit=False)
        notice.writer = kwargs.get('writer', None)
        notice.category = kwargs.get('category', None)
        notice.title = kwargs.get('title', None)
        notice.channel_id = kwargs.get('channel_id', None)
        notice.channel_name = kwargs.get('channel_name', None)
        notice.image = kwargs.get('image', None)
        notice.save()
        return notice


    def update(self, **kwargs):
        notice = super().save(commit=False)
        notice.category = kwargs.get('category', None)
        notice.title = kwargs.get('title', None)
        notice.old_title = kwargs.get('old_title', None)
        notice.channel_id = kwargs.get('channel_id', None)
        notice.channel_name = kwargs.get('channel_name', None)
        notice.save()
        return notice