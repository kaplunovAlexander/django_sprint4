# Generated by Django 3.2.16 on 2025-01-22 18:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0011_remove_post_comment_count'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comments',
            options={'ordering': ('created_at',)},
        ),
    ]
