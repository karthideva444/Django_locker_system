# Generated by Django 4.2.9 on 2024-01-21 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage_locker', '0044_rename_reason_payment_intent'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='biz_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='loc_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_status',
            field=models.CharField(blank=True, db_comment='Open(O) or Failed(F) or Paid(P) ', max_length=1, null=True),
        ),
    ]
