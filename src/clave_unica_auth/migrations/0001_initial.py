# Generated by Django 2.2.2 on 2019-06-27 02:00

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ClaveUnicaLogin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.UUIDField(default=uuid.uuid4)),
                ('authorization_code', models.CharField(max_length=120)),
                ('access_token', models.CharField(max_length=120)),
            ],
        ),
    ]
