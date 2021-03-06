# Generated by Django 3.0.6 on 2021-02-05 17:21

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0063_auto_20210205_1429'),
    ]

    operations = [
        migrations.AddField(
            model_name='folder',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='folder',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='box',
            name='category',
            field=models.CharField(choices=[('guest', '게스트'), ('bluemover', '블루무버')], max_length=50),
        ),
    ]
