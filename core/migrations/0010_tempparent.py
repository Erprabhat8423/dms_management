# Generated by Django 4.2.20 on 2025-03-24 11:13

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_remove_children_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='TempParent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=200)),
                ('dob', models.CharField(max_length=20)),
                ('email', models.CharField(max_length=254)),
                ('phone_number', models.CharField(max_length=15, unique=True)),
                ('is_student', models.BooleanField(default=False)),
                ('otp_hash', models.CharField(blank=True, max_length=64, null=True)),
                ('otp_created_at', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('max_attempts', models.PositiveIntegerField(default=5)),
                ('attempt_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
