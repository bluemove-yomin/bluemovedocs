# Generated by Django 3.0.6 on 2021-01-22 14:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notice', '0035_auto_20210118_2143'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notice',
            name='category',
            field=models.CharField(choices=[('bluemover', '블루무버'), ('guest', '게스트')], max_length=50),
        ),
    ]
