# Generated by Django 3.0.6 on 2021-01-12 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0010_auto_20210112_1659'),
    ]

    operations = [
        migrations.AlterField(
            model_name='box',
            name='category',
            field=models.CharField(choices=[('bluemover', '블루무버'), ('posongvi', '뽀송비 학생'), ('applicant', '블루무버 희망자')], max_length=50),
        ),
    ]
