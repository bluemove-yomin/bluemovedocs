from django.db import models
from django.contrib.auth.models import User

class Notice(models.Model):

    CATEGORY_CHOICES = {
        ('bluemover', '블루무버'),
        ('applicant', '블루무버 희망자'),
        ('posongvi', '뽀송비 학생')
    }

    title = models.CharField(max_length = 50, null = False)
    writer = models.ForeignKey(User, on_delete=models.CASCADE, null = True)
    category = models.CharField(max_length = 50, choices = CATEGORY_CHOICES, null = False)
    content = models.TextField(null = False)
    image = models.ImageField(upload_to='images/', null = True)
    created_at = models.DateField(auto_now_add = True)
    updated_at = models.DateField(auto_now = True)


class Comment(models.Model):
    content = models.TextField(null = False)
    writer = models.ForeignKey(User, on_delete = models.CASCADE)
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateField(auto_now_add = True)
    updated_at = models.DateField(auto_now = True)