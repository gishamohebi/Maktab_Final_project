# Generated by Django 4.0.2 on 2022-02-22 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_alter_user_email_alter_user_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='active_email',
            field=models.BooleanField(),
        ),
        migrations.AlterField(
            model_name='user',
            name='active_phone',
            field=models.BooleanField(),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, error_messages={'unique': 'This email already has an account'}, max_length=254, unique=True, verbose_name='email address'),
        ),
    ]