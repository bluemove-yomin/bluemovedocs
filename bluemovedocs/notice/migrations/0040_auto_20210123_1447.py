# Generated by Django 3.0.6 on 2021-01-23 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notice', '0039_auto_20210122_2053'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notice',
            name='category',
            field=models.CharField(choices=[('bluemover', '블루무버'), ('guest', '게스트')], max_length=50),
        ),
    ]