# Generated by Django 4.2.15 on 2024-09-02 06:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0005_alter_author_options_rename_first_name_author_name_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='genre',
            name='genre_id',
        ),
    ]
