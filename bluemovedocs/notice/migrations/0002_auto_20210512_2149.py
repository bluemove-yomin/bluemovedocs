# Generated by Django 3.0.6 on 2021-05-12 21:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notice', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notice',
            name='category',
            field=models.CharField(choices=[('bluemover', '블루무버'), ('guest', '게스트')], max_length=50),
        ),
    ]
