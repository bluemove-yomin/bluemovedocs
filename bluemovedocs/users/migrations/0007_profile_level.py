# Generated by Django 3.0.6 on 2021-01-17 00:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_profile_name_update_flag'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='level',
            field=models.CharField(max_length=50, null=True),
        ),
    ]