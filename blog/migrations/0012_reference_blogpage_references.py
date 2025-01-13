# Generated by Django 4.2.3 on 2025-01-13 07:25

from django.db import migrations, models
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0011_alter_blogpage_intro'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('author', models.CharField(blank=True, max_length=255, null=True)),
                ('publication_date', models.DateField(blank=True, null=True)),
                ('url', models.URLField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Reference',
                'verbose_name_plural': 'References',
            },
        ),
        migrations.AddField(
            model_name='blogpage',
            name='references',
            field=modelcluster.fields.ParentalManyToManyField(blank=True, to='blog.reference'),
        ),
    ]
