# Generated by Django 3.0.6 on 2021-02-01 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0057_auto_20210201_1412'),
    ]

    operations = [
        migrations.RenameField(
            model_name='box',
            old_name='folder',
            new_name='folder_id',
        ),
        migrations.AlterField(
            model_name='doc',
            name='folder',
            field=models.CharField(blank=True, choices=[('0ADNIg7OWApdMUk9PVA', '3 콘텐츠사업'), ('0ADF4LPECMczOUk9PVA', '2 교육사업'), ('0AIsg5YLQSTjaUk9PVA', '5 운영')], max_length=50, null=True),
        ),
    ]
