# Generated by Django 4.2.9 on 2024-02-10 10:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage_locker', '0059_cucmd_cucmd_cu_cmd_pk'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='activity',
            name='amount',
        ),
    ]
