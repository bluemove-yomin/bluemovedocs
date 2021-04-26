# Generated by Django 3.0.6 on 2021-04-26 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0073_auto_20210425_1755'),
    ]

    operations = [
        migrations.AddField(
            model_name='box',
            name='forler_prefix',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='box',
            name='category',
            field=models.CharField(choices=[('bluemover', '블루무버'), ('guest', '게스트')], max_length=50),
        ),
    ]