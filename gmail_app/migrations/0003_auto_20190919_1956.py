# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-09-19 19:56
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('gmail_app', '0002_auto_20190917_2237'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('event_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('status', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='emailitem',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2019, 9, 19, 19, 56, 31, 458660, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='emailitem',
            name='updated',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
