# Generated by Django 3.0.6 on 2021-01-22 13:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0041_auto_20210121_2310'),
    ]

    operations = [
        migrations.AddField(
            model_name='doc',
            name='reject_flag',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='doc',
            name='rejection_datetime',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
    ]
