# Generated by Django 5.0.3 on 2024-06-07 12:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homeoffice', '0019_vehicle'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehicle',
            name='employee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='homeoffice.employee', verbose_name="Employee's default car"),
        ),
    ]
