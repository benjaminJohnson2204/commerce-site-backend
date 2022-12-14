# Generated by Django 4.0.6 on 2022-07-26 20:14

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('rugs_app', '0004_remove_user_confirmation_order_date_picked_up_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='date_picked_up',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='date_placed',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
        migrations.AlterField(
            model_name='order',
            name='date_ready',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='rug',
            name='date_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
    ]
