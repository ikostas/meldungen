# Generated by Django 5.0.3 on 2024-05-10 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homeoffice', '0010_alter_defaultworktime_end_time_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='defaultworktime',
            name='working_time',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='defaultworktime',
            name='break_time',
            field=models.DecimalField(decimal_places=1, max_digits=4, null=True),
        ),
    ]