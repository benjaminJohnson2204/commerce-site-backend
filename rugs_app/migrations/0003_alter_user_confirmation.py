# Generated by Django 4.0.6 on 2022-07-24 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rugs_app', '0002_user_confirmation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='confirmation',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
