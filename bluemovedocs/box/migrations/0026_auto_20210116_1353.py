# Generated by Django 3.0.6 on 2021-01-16 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0025_auto_20210115_1930'),
    ]

    operations = [
        migrations.AlterField(
            model_name='box',
            name='category',
            field=models.CharField(choices=[('applicant', '블루무버 희망자'), ('bluemover', '블루무버'), ('posongvi', '뽀송비 학생')], max_length=50),
        ),
    ]