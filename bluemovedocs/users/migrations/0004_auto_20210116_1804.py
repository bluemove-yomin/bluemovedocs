# Generated by Django 3.0.6 on 2021-01-16 18:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_profile_realname'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='realname',
            new_name='real_name',
        ),
    ]
