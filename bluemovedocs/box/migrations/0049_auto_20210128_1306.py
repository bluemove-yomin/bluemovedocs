# Generated by Django 3.0.6 on 2021-01-28 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0048_box_channel_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='doc',
            name='slack_ts',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='box',
            name='category',
            field=models.CharField(choices=[('guest', '게스트'), ('bluemover', '블루무버')], max_length=50),
        ),
    ]
