# Generated by Django 3.0.6 on 2021-01-03 17:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0021_auto_20210103_1507'),
    ]

    operations = [
        migrations.AddField(
            model_name='box',
            name='deadline_check',
            field=models.DateField(null=True),
        ),
    ]
