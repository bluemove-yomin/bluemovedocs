# Generated by Django 3.0.6 on 2021-02-01 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notice', '0046_auto_20210201_1412'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notice',
            name='category',
            field=models.CharField(choices=[('guest', '게스트'), ('bluemover', '블루무버')], max_length=50),
        ),
    ]
