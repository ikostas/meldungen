# Generated by Django 5.0.3 on 2024-04-23 12:21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AbsenceType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='Name')),
                ('description', models.TextField(max_length=500, verbose_name='Description')),
                ('color', models.CharField(max_length=30, verbose_name='Farbe')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeAbsenceGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='Name')),
                ('description', models.TextField(max_length=500, verbose_name='Description')),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='Name')),
                ('description', models.TextField(max_length=500, verbose_name='Description')),
            ],
        ),
        migrations.CreateModel(
            name='AbsenceEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(verbose_name='Anfangsdatum')),
                ('end_date', models.DateField(verbose_name='Datum des Endes')),
                ('event_type', models.CharField(choices=[('holiday', 'Feiertag'), ('employee_event', 'Mitarbeiter'), ('employee_group_event', 'Mitarbeitergruppe')], default='employee_event', max_length=20, verbose_name='Type of event')),
                ('day_type', models.CharField(choices=[('full', '1'), ('half', '1/2'), ('quarter', '1/4')], default='full', max_length=20, verbose_name='Type of the day')),
                ('comment', models.CharField(blank=True, max_length=220, verbose_name='Kommentar')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='user_created', to=settings.AUTH_USER_MODEL, verbose_name='Created by')),
                ('employee_link', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='user_link', to=settings.AUTH_USER_MODEL, verbose_name='User')),
                ('absence_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='absence_type_event', to='homeoffice.absencetype', verbose_name='Absence type')),
                ('employee_absence_group_link', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='EAG_date', to='homeoffice.employeeabsencegroup', verbose_name='Employee absence group')),
            ],
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('user_link', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('employee_absence_group_link', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='absence_group', to='homeoffice.employeeabsencegroup', verbose_name='User absence group')),
                ('employee_group_link', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='users_group', to='homeoffice.employeegroup', verbose_name='User group')),
            ],
        ),
    ]
