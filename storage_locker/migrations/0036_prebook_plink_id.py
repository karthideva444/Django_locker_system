# Generated by Django 4.2.9 on 2024-01-09 21:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage_locker', '0035_prebook_reference_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='prebook',
            name='plink_id',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
