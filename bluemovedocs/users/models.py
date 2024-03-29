from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.shortcuts import render, redirect


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sub_id = models.CharField(max_length = 10, null=True)
    phone = models.CharField(max_length = 100, null=True)
    info_update_flag = models.BooleanField(default = False)
    level = models.CharField(max_length = 50, null=True)
    slack_user_id = models.CharField(max_length = 50, null=True)
    notion_user_id = models.CharField(max_length = 100, null=True)


@receiver(post_save, sender=User)
def create_save_user_profile(sender, instance, created, **kwargs):
    user = instance
    if created:
        profile = Profile(user=user)
        profile.save()