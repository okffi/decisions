# -*- coding: utf-8 -*-
# Generated by Django 1.9.3 on 2016-05-24 09:03
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0009_auto_20160321_1714'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionhit',
            name='extra',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='subscriptionhit',
            name='hit_type',
            field=models.IntegerField(choices=[(0, 'Search result'), (1, 'Comment reply')], default=0),
        ),
    ]
