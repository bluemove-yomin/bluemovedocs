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
        box.title = kwargs.get('title', None)
        box.document_id = kwargs.get('document_id', None)
        box.deadline = kwargs.get('deadline', None)
        box.image = kwargs.get('image', None)
        box.save()
        return box


    def update(self, **kwargs):
        box = super().save(commit=False)
        box.category = kwargs.get('category', None)
        box.title = kwargs.get('title', None)
        box.document_id = kwargs.get('document_id', None)
        box.deadline = kwargs.get('deadline', None)
        box.save()
        return box