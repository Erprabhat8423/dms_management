# Generated by Django 4.2.20 on 2025-03-28 05:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_alter_tempparent_profile_pic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parent_profile',
            name='profile_pic',
            field=models.ImageField(blank=True, null=True, upload_to='parent_profiles/'),
        ),
    ]
