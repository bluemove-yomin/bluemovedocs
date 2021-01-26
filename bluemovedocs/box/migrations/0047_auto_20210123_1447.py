# Generated by Django 3.0.6 on 2021-01-23 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0046_auto_20210122_2053'),
    ]

    operations = [
        migrations.AlterField(
            model_name='box',
            name='category',
            field=models.CharField(choices=[('bluemover', '블루무버'), ('guest', '게스트')], max_length=50),
        ),
        migrations.AlterField(
            model_name='doc',
            name='avatar_src',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='doc',
            name='creation_date',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='doc',
            name='inside_permission_id',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='doc',
            name='outside_permission_id',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='doc',
            name='permission_id',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]