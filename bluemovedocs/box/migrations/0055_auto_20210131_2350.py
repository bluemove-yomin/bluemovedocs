# Generated by Django 3.0.6 on 2021-01-31 23:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0054_auto_20210131_2324'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='box',
            name='channel_id_text',
        ),
        migrations.AlterField(
            model_name='box',
            name='category',
            field=models.CharField(choices=[('bluemover', '블루무버'), ('guest', '게스트')], max_length=50),
        ),
        migrations.AlterField(
            model_name='doc',
            name='folder',
            field=models.CharField(blank=True, choices=[('0ADNIg7OWApdMUk9PVA', '3 콘텐츠사업'), ('0ADF4LPECMczOUk9PVA', '2 교육사업'), ('0AIsg5YLQSTjaUk9PVA', '5 운영')], max_length=50, null=True),
        ),
    ]