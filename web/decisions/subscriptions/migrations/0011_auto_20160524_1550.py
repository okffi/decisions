# -*- coding: utf-8 -*-
# Generated by Django 1.9.3 on 2016-05-24 12:50
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0010_auto_20160524_1203'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='extra',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='subscription',
            name='search_backend',
            field=models.IntegerField(choices=[(0, 'Text Search'), (1, 'Map Search')], default=0, verbose_name='Search type'),
        ),
    ]
