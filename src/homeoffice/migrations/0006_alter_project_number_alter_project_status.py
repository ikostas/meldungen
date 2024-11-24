# Generated by Django 5.0.3 on 2024-05-06 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homeoffice', '0005_project_worktimesetup'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='number',
            field=models.CharField(blank=True, max_length=120, verbose_name='Number'),
        ),
        migrations.AlterField(
            model_name='project',
            name='status',
            field=models.BooleanField(blank=True, default=True, verbose_name='Active'),
        ),
    ]
