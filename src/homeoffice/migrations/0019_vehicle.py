# Generated by Django 5.0.3 on 2024-06-07 12:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homeoffice', '0018_rename_places_place'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=120, verbose_name='Name')),
                ('number', models.CharField(blank=True, max_length=120, verbose_name='Number')),
                ('employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='homeoffice.project', verbose_name="Employee's default car")),
            ],
        ),
    ]
