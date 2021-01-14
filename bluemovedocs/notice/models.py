from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField

class Notice(models.Model):

    CATEGORY_CHOICES = {
        ('bluemover', '블루무버'),
        ('applicant', '블루무버 희망자'),
        ('posongvi', '뽀송비 학생')
    }

    title = models.CharField(max_length = 50)
    writer = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length = 50, choices = CATEGORY_CHOICES)
    content = RichTextField()
    # content = models.TextField()
    image = models.ImageField(upload_to='images/')
    created_at = models.DateField(auto_now_add = True)
    updated_at = models.DateField(auto_now = True)
    favorite_user_set = models.ManyToManyField(User, blank=True, related_name="favorite_user_set", through="Favorite")

    @property
    def favorite_count(self):
        return self.favorite_user_set.count()


class Comment(models.Model):
    content = models.TextField(null = False)
    avatar_src = models.TextField(null = True)
    writer = models.ForeignKey(User, on_delete = models.CASCADE)
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateField(auto_now_add = True)
    updated_at = models.DateField(auto_now = True)


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    class Meta:
        unique_together = (('user','notice'))