# Generated by Django 3.0.6 on 2021-01-12 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notice', '0007_auto_20210112_1326'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notice',
            name='category',
            field=models.CharField(choices=[('applicant', '블루무버 희망자'), ('posongvi', '뽀송비 학생'), ('bluemover', '블루무버')], max_length=50),
        ),
    ]