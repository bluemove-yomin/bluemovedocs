# Generated by Django 3.0.6 on 2021-01-03 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0027_auto_20210103_1931'),
    ]

    operations = [
        migrations.AlterField(
            model_name='box',
            name='category',
            field=models.CharField(choices=[('posongvi', '뽀송비 학생'), ('applicant', '블루무버 희망자'), ('bluemover', '블루무버')], max_length=50),
        ),
    ]
