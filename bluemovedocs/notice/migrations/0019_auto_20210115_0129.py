# Generated by Django 3.0.6 on 2021-01-15 01:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notice', '0018_auto_20210114_2154'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notice',
            name='category',
            field=models.CharField(choices=[('bluemover', '블루무버'), ('applicant', '블루무버 희망자'), ('posongvi', '뽀송비 학생')], max_length=50),
        ),
    ]