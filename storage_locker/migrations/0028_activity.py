# Generated by Django 4.2.6 on 2023-12-21 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage_locker', '0027_alter_bizlkr_updated_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('book_id', models.IntegerField(blank=True, null=True)),
                ('loc_id', models.IntegerField(blank=True, null=True)),
                ('lock_no', models.CharField(blank=True, max_length=10, null=True)),
                ('activity_status', models.CharField(blank=True, db_comment='Either Opened or Booked or Paid or Released', max_length=10, null=True)),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True)),
                ('initiated_by', models.CharField(blank=True, max_length=10, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                'db_table': 'activity',
            },
        ),
    ]
