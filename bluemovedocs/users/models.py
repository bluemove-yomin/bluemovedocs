from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(verbose_name="avatar", upload_to="images/")


@receiver(post_save, sender=User)
def create_save_user_profile(sender, instance, created, **kwargs):
    user = instance
    if created:
        profile = Profile(user=user)
        profile.save()