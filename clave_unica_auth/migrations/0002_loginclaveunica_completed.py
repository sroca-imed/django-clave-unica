# Generated by Django 2.2.2 on 2019-06-30 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clave_unica_auth', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='loginclaveunica',
            name='completed',
            field=models.BooleanField(default=False),
        ),
    ]