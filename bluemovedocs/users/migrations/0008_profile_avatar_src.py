# Generated by Django 3.0.6 on 2021-01-17 21:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_profile_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='avatar_src',
            field=models.CharField(max_length=300, null=True),
        ),
    ]
