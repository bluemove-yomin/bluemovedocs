# Generated by Django 3.0.6 on 2021-01-02 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0003_auto_20210102_1432'),
    ]

    operations = [
        migrations.AlterField(
            model_name='box',
            name='category',
            field=models.CharField(choices=[('applicant', '블루무버 희망자'), ('posongvi', '뽀송비 학생'), ('bluemover', '블루무버')], max_length=50),
        ),
    ]
