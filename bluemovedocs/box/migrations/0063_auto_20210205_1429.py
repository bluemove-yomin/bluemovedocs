# Generated by Django 3.0.6 on 2021-02-05 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0062_auto_20210202_0132'),
    ]

    operations = [
        migrations.CreateModel(
            name='Folder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('one', models.CharField(max_length=500)),
                ('two', models.CharField(max_length=500)),
                ('three', models.CharField(max_length=500)),
                ('four', models.CharField(max_length=500)),
                ('five', models.CharField(max_length=500)),
                ('six', models.CharField(max_length=500)),
                ('seven', models.CharField(max_length=500)),
                ('eight', models.CharField(max_length=500)),
            ],
        ),
        migrations.AlterField(
            model_name='box',
            name='category',
            field=models.CharField(choices=[('bluemover', '블루무버'), ('guest', '게스트')], max_length=50),
        ),
        migrations.AlterField(
            model_name='doc',
            name='slack_ts',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
