# Generated by Django 5.0.1 on 2024-02-17 08:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointmenttimeslot',
            name='is_available',
            field=models.BooleanField(default=True),
        ),
    ]
