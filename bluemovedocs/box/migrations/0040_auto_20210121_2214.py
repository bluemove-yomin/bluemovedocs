# Generated by Django 3.0.6 on 2021-01-21 22:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0039_auto_20210118_2143'),
    ]

    operations = [
        migrations.RenameField(
            model_name='doc',
            old_name='box_permission_id',
            new_name='inside_permission_id',
        ),
        migrations.RenameField(
            model_name='doc',
            old_name='user_permission_id',
            new_name='outside_permission_id',
        ),
        migrations.AddField(
            model_name='doc',
            name='permission_id',
            field=models.CharField(max_length=300, null=True),
        ),
    ]