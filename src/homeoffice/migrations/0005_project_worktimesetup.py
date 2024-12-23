# Generated by Django 5.0.3 on 2024-05-06 14:17

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homeoffice', '0004_alter_absenceevent_options'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(blank=True, max_length=120, verbose_name='Name')),
                ('description', models.TextField(blank=True, max_length=500, verbose_name='Description')),
                ('status', models.BooleanField(blank=True, default=True, verbose_name='Status')),
            ],
        ),
        migrations.CreateModel(
            name='WorkTimeSetup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.CharField(choices=[(1, 'Mo'), (2, 'Di'), (3, 'Mi'), (4, 'Do'), (5, 'Fr'), (6, 'Sa'), (7, 'So')], max_length=4, verbose_name='Weekday')),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='employee_time', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
        ),
    ]
