# Generated by Django 5.0.1 on 2024-02-17 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0003_remove_workschedule_date_workschedule_from_date_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workschedule',
            name='shift',
        ),
        migrations.AddField(
            model_name='workschedule',
            name='shift',
            field=models.ManyToManyField(related_name='work_schedules', to='clinic.shift'),
        ),
    ]
