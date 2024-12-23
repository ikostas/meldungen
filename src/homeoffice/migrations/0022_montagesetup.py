# Generated by Django 5.0.3 on 2024-06-10 08:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homeoffice', '0021_task'),
    ]

    operations = [
        migrations.CreateModel(
            name='MontageSetup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('montage_group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='default_montage_group', to='homeoffice.employeegroup', verbose_name='Montage group')),
            ],
        ),
    ]
