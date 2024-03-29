# Generated by Django 3.0.6 on 2021-05-12 21:49

import ckeditor.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Box',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('category', models.CharField(choices=[('bluemover', '블루무버'), ('guest', '게스트')], max_length=50)),
                ('drive_name', models.CharField(blank=True, max_length=50, null=True)),
                ('folder_name', models.CharField(blank=True, max_length=50, null=True)),
                ('folder_id', models.CharField(blank=True, max_length=100, null=True)),
                ('folder_prefix', models.CharField(blank=True, max_length=10, null=True)),
                ('official_template_flag', models.BooleanField(default=False)),
                ('document_name', models.CharField(blank=True, max_length=50, null=True)),
                ('document_id', models.CharField(max_length=300)),
                ('document_mimetype', models.CharField(blank=True, max_length=300, null=True)),
                ('channel_id', models.CharField(max_length=50)),
                ('channel_name', models.CharField(max_length=50)),
                ('deadline', models.DateField()),
                ('deadline_update_flag', models.BooleanField(default=False)),
                ('content', ckeditor.fields.RichTextField()),
                ('content_update_flag', models.BooleanField(default=False)),
                ('image', models.ImageField(blank=True, null=True, upload_to='images/')),
                ('created_at', models.DateField(auto_now_add=True)),
                ('updated_at', models.DateField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateField(auto_now_add=True)),
                ('updated_at', models.DateField(auto_now=True)),
                ('box', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='box.Box')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='box_favorite_user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'box')},
            },
        ),
        migrations.CreateModel(
            name='Doc',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar_src', models.CharField(blank=True, max_length=1500, null=True)),
                ('name', models.CharField(max_length=300)),
                ('mimetype', models.CharField(blank=True, max_length=300, null=True)),
                ('file_id', models.CharField(max_length=300)),
                ('outside_permission_id', models.CharField(blank=True, max_length=300, null=True)),
                ('permission_id', models.CharField(blank=True, max_length=300, null=True)),
                ('inside_permission_id', models.CharField(blank=True, max_length=300, null=True)),
                ('slack_ts', models.CharField(blank=True, max_length=200, null=True)),
                ('reject_reason', models.CharField(blank=True, max_length=100, null=True)),
                ('creation_date', models.CharField(blank=True, max_length=100, null=True)),
                ('submission_date', models.CharField(blank=True, max_length=100, null=True)),
                ('submit_flag', models.BooleanField(blank=True, default=False, null=True)),
                ('rejection_date', models.CharField(blank=True, max_length=100, null=True)),
                ('reject_flag', models.BooleanField(blank=True, default=False, null=True)),
                ('return_date', models.CharField(blank=True, max_length=100, null=True)),
                ('return_flag', models.BooleanField(blank=True, default=False, null=True)),
                ('delete_flag', models.BooleanField(blank=True, default=False, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('box', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='docs', to='box.Box')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='box',
            name='box_favorite_user_set',
            field=models.ManyToManyField(blank=True, related_name='box_favorite_user_set', through='box.Favorite', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='box',
            name='writer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
