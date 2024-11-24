# Generated by Django 5.0.3 on 2024-06-07 13:17

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homeoffice', '0020_alter_vehicle_employee'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(verbose_name='Anfangsdatum')),
                ('end_date', models.DateField(verbose_name='Datum des Endes')),
                ('employee_link', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='workers_task', to=settings.AUTH_USER_MODEL, verbose_name='Worker')),
                ('place', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='place_task', to='homeoffice.place', verbose_name='Task place')),
                ('vehicle', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='vehicle_task', to='homeoffice.vehicle', verbose_name='Vehicle')),
            ],
        ),
    ]
