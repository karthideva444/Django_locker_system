# Generated by Django 4.2.9 on 2024-02-02 07:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage_locker', '0047_payment_extended_duration'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='book',
            name='duration',
        ),
    ]
