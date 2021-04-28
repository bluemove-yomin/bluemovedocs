# Generated by Django 3.0.6 on 2021-04-29 01:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notice', '0065_auto_20210426_1753'),
    ]

    operations = [
        migrations.AddField(
            model_name='notice',
            name='old_title',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='notice',
            name='category',
            field=models.CharField(choices=[('guest', '게스트'), ('bluemover', '블루무버')], max_length=50),
        ),
    ]
