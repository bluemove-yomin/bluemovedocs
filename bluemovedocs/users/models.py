# from django.contrib.auth.models import User
# from django.db import models
# from django.dispatch import receiver
# from django.db.models.signals import post_save


# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     image = models.ImageField(verbose_name="Profile Picture", upload_to="images/", default="images/profile-picture-default.png")
#     info = models.TextField(null=True, blank=True)

# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     instance.profile.save()