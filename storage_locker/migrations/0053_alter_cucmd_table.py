# Generated by Django 4.2.9 on 2024-02-06 13:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage_locker', '0052_changelog_cucmd_lockcmd_lockerstatus_routerinfo_and_more'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='cucmd',
            table='cu_cmd',
        ),
    ]
