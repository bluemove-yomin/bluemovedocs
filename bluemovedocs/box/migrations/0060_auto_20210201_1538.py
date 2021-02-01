# Generated by Django 3.0.6 on 2021-02-01 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0059_auto_20210201_1420'),
    ]

    operations = [
        migrations.AlterField(
            model_name='box',
            name='category',
            field=models.CharField(choices=[('guest', '게스트'), ('bluemover', '블루무버')], max_length=50),
        ),
        migrations.AlterField(
            model_name='doc',
            name='folder',
            field=models.CharField(blank=True, choices=[('0AIsg5YLQSTjaUk9PVA', '5 운영'), ('0ADNIg7OWApdMUk9PVA', '3 콘텐츠사업'), ('0ADF4LPECMczOUk9PVA', '2 교육사업')], max_length=50, null=True),
        ),
    ]
