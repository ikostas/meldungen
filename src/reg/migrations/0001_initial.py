# Generated by Django 5.0.3 on 2024-04-23 12:21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Issue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='Name')),
                ('date', models.DateField(verbose_name='Date when issue was found')),
                ('project', models.CharField(max_length=120, verbose_name='Project No.')),
                ('description', models.TextField(max_length=500, verbose_name='issue descripion')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Hergestellt in')),
                ('status', models.CharField(choices=[('open', 'Geöffnet'), ('closed', 'Geschlossen')], default='open', max_length=20, verbose_name='Status')),
                ('issue_type', models.CharField(choices=[('defect', 'Fehler'), ('suggest', 'Verbesserung'), ('danger', 'Unsichere Situation')], default='defect', max_length=25, verbose_name='Meldungstyp')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='users_issues', to=settings.AUTH_USER_MODEL, verbose_name='Erstellt von')),
            ],
        ),
        migrations.CreateModel(
            name='IssueComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(max_length=500, verbose_name='Kommentar')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Hergestellt in')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='users_issue_comments', to=settings.AUTH_USER_MODEL, verbose_name='Erstellt von')),
                ('issue', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='issue_user_comments', to='reg.issue')),
            ],
        ),
        migrations.CreateModel(
            name='IssuePic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pic', models.ImageField(upload_to='issues/', verbose_name='Bilder')),
                ('issue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='issue_pics', to='reg.issue')),
            ],
        ),
    ]