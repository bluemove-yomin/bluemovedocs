# Generated by Django 3.0.6 on 2021-01-15 03:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0022_auto_20210115_0252'),
    ]

    operations = [
        migrations.AddField(
            model_name='doc',
            name='name',
            field=models.CharField(default='테스트', max_length=300),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='box',
            name='category',
            field=models.CharField(choices=[('bluemover', '블루무버'), ('applicant', '블루무버 희망자'), ('posongvi', '뽀송비 학생')], max_length=50),
        ),
    ]