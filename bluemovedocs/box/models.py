from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import pre_save
import datetime
from django.utils.dateparse import parse_date
from ckeditor.fields import RichTextField

class Box(models.Model):

    CATEGORY_CHOICES = {
        ('bluemover', '블루무버'),
        ('applicant', '블루무버 희망자'),
        ('posongvi', '뽀송비 학생')
    }

    title = models.CharField(max_length = 50)
    writer = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length = 50, choices = CATEGORY_CHOICES)
    document_id = models.CharField(max_length = 300)
    content = RichTextField()
    # content = models.TextField()
    content_update_flag = models.BooleanField(default = False)
    image = models.ImageField(upload_to='images/', null = True, blank = True)
    deadline = models.DateField()
    deadline_update_flag = models.BooleanField(default = False)
    created_at = models.DateField(auto_now_add = True)
    updated_at = models.DateField(auto_now = True)
    box_favorite_user_set = models.ManyToManyField(User, blank = True, related_name="box_favorite_user_set", through="Favorite")

    @property
    def favorite_count(self):
        return self.box_favorite_user_set.count()

    @property
    def deadline_is_yet_to_come(self):
        return datetime.date.today() + datetime.timedelta(days = 2) <= self.deadline

    @property
    def deadline_is_tomorrow(self):
        return datetime.date.today() + datetime.timedelta(days = 1) == self.deadline

    @property
    def deadline_is_today(self):
        return datetime.date.today() == self.deadline

    @property
    def deadline_is_over(self):
        return datetime.date.today() > self.deadline

    @property
    def days_left_until_deadline(self):
        return self.deadline - datetime.date.today()


@receiver(pre_save, sender=Box)
def deadline_update_flag_on(sender, instance, **kwargs):
    try:
        obj = sender.objects.get(pk=instance.pk)
        obj_date_raw = str(obj.deadline)
        ins_date_raw = str(instance.deadline)
    except sender.DoesNotExist:
        pass # Object is new, so field hasn't technically changed, but you may want to do something else here.
    else:
        if not obj_date_raw == ins_date_raw:
            instance.deadline_update_flag = True


@receiver(pre_save, sender=Box)
def content_update_flag_on(sender, instance, **kwargs):
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass # Object is new, so field hasn't technically changed, but you may want to do something else here.
    else:
        if not obj.content == instance.content: # Field has changed
            instance.content_update_flag = True


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="box_favorite_user")
    box = models.ForeignKey(Box, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    class Meta:
        unique_together = (('user','box'))