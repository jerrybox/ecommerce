# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-09-13 17:56


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offer', '0027_auto_20190913_1756'),
        ('voucher', '0006_auto_20181205_1017'),
    ]

    operations = [
        migrations.CreateModel(
            name='VoucherSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('count', models.PositiveIntegerField(verbose_name='Number of vouchers')),
                ('code_length', models.IntegerField(default=12, verbose_name='Length of Code')),
                ('description', models.TextField(verbose_name='Description')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('start_datetime', models.DateTimeField(verbose_name='Start datetime')),
                ('end_datetime', models.DateTimeField(verbose_name='End datetime')),
                ('offer', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='voucher_set', to='offer.ConditionalOffer', verbose_name='Offer')),
            ],
            options={
                'abstract': False,
                'get_latest_by': 'date_created',
                'verbose_name': 'VoucherSet',
                'verbose_name_plural': 'VoucherSets',
            },
        ),
        migrations.AddField(
            model_name='voucher',
            name='voucher_set',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vouchers', to='voucher.VoucherSet'),
        ),
    ]
