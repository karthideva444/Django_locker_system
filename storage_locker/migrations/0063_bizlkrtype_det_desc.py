# Generated by Django 4.2.9 on 2024-02-10 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage_locker', '0062_remove_activity_updated_at_activity_biz_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bizlkrtype',
            name='det_desc',
            field=models.TextField(blank=True, max_length=500, null=True),
        ),
    ]
