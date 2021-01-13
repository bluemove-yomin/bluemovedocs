# Generated by Django 3.0.6 on 2021-01-11 23:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0006_auto_20210109_1609'),
    ]

    operations = [
        migrations.AddField(
            model_name='box',
            name='document_id',
            field=models.CharField(default='', max_length=300),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='box',
            name='category',
            field=models.CharField(choices=[('bluemover', '블루무버'), ('applicant', '블루무버 희망자'), ('posongvi', '뽀송비 학생')], max_length=50),
        ),
    ]