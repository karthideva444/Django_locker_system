# Generated by Django 4.2.6 on 2023-12-21 13:14

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('storage_locker', '0028_activity'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
