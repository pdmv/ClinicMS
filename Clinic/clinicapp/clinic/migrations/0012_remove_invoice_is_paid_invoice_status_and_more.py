# Generated by Django 5.0.1 on 2024-02-20 15:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0011_remove_prescription_medicines_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoice',
            name='is_paid',
        ),
        migrations.AddField(
            model_name='invoice',
            name='status',
            field=models.CharField(choices=[('pending', 'Chờ thanh toán'), ('paid', 'Đã thanh toán'), ('cancelled', 'Đã huỷ')], default='Chờ thanh toán', max_length=20),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='appointment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoice', to='clinic.appointment'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='payment_method',
            field=models.CharField(choices=[('Tiền mặt', 'Tiền mặt'), ('e-Wallet', 'e-Wallet')], max_length=20),
        ),
    ]
