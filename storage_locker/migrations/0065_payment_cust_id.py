# Generated by Django 4.2.9 on 2024-02-17 08:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage_locker', '0064_alter_changelog_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='cust_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
