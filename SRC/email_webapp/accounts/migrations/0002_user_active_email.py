# Generated by Django 4.0.1 on 2022-02-22 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='active_email',
            field=models.BooleanField(default=False),
        ),
    ]
