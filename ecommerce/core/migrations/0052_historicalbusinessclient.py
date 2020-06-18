# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-08 16:00


import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0051_ecommercefeatureroleassignment_enterprise_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalBusinessClient',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=255, verbose_name='Name')),
                ('enterprise_customer_uuid', models.UUIDField(blank=True, help_text='UUID for an EnterpriseCustomer from the Enterprise Service.', null=True, verbose_name='EnterpriseCustomer UUID')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical business client',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
