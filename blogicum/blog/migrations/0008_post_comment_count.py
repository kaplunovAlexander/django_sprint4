# Generated by Django 5.1.3 on 2024-12-05 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_comments'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='comment_count',
            field=models.IntegerField(default=0, verbose_name='Кол-во комментариев'),
        ),
    ]
