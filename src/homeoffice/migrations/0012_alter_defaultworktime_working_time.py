# Generated by Django 5.0.3 on 2024-05-15 14:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homeoffice', '0011_defaultworktime_working_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='defaultworktime',
            name='working_time',
            field=models.DecimalField(decimal_places=1, max_digits=4, null=True),
        ),
    ]
