# Generated by Django 4.2.6 on 2023-12-09 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage_locker', '0014_alter_iotrequest_remarks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessinfo',
            name='iot_client_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
