# Generated by Django 4.2.6 on 2023-12-17 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage_locker', '0021_book_booked_durations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='book',
            name='booked_durations',
        ),
        migrations.AddField(
            model_name='book',
            name='booked_duration',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='prebook',
            name='booking_hrs',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
