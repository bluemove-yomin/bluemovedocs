# Generated by Django 3.0.6 on 2021-04-26 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notice', '0062_auto_20210426_0140'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notice',
            name='category',
            field=models.CharField(choices=[('bluemover', '블루무버'), ('guest', '게스트')], max_length=50),
        ),
    ]
