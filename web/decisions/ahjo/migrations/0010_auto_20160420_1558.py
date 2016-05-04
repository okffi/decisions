# -*- coding: utf-8 -*-
# Generated by Django 1.9.3 on 2016-04-20 12:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ahjo', '0009_auto_20160420_1528'),
    ]

    database_operations = [
        migrations.AlterModelTable('comment', 'comments_comment'),
    ]

    state_operations = [
        migrations.DeleteModel(
            name='Comment',
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=database_operations,
            state_operations=state_operations)
    ]