# Generated by Django 3.0.6 on 2021-01-09 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0005_auto_20210109_1607'),
    ]

    operations = [
        migrations.AlterField(
            model_name='box',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='images/'),
        ),
    ]