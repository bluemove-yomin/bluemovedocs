# Generated by Django 3.0.6 on 2021-02-01 01:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_auto_20210118_1530'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='slack_user_id',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
