# Generated by Django 3.0.6 on 2021-01-17 22:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notice', '0030_auto_20210117_2200'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notice',
            name='category',
            field=models.CharField(choices=[('bluemover', '블루무버'), ('posongvi', '뽀송비 학생'), ('applicant', '블루무버 희망자')], max_length=50),
        ),
    ]
