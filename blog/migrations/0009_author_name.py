# Generated by Django 4.2.3 on 2025-01-08 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0008_author_blogpage_author'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
