# Generated by Django 3.0.6 on 2021-01-16 18:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0029_auto_20210116_1840'),
    ]

    operations = [
        migrations.AlterField(
            model_name='box',
            name='category',
            field=models.CharField(choices=[('bluemover', '블루무버'), ('applicant', '블루무버 희망자'), ('posongvi', '뽀송비 학생')], max_length=50),
        ),
    ]
