# Generated by Django 3.0.6 on 2021-01-15 03:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0023_auto_20210115_0330'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='doc',
            name='src',
        ),
        migrations.AddField(
            model_name='doc',
            name='file_id',
            field=models.CharField(default='1Poy06EH8AZB-ascb2Nugg6AHTAo4rIRAa46X8WCdkeA', max_length=300),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='box',
            name='category',
            field=models.CharField(choices=[('bluemover', '블루무버'), ('posongvi', '뽀송비 학생'), ('applicant', '블루무버 희망자')], max_length=50),
        ),
    ]