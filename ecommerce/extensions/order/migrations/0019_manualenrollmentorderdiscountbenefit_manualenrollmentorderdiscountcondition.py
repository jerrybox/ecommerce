# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-08-08 07:42
from __future__ import unicode_literals

from django.db import migrations

import ecommerce.extensions.offer.mixins


class Migration(migrations.Migration):

    dependencies = [
        ('offer', '0025_auto_20190624_1747'),
        ('order', '0018_historicalline_historicalorder'),
    ]

    operations = [
        migrations.CreateModel(
            name='ManualEnrollmentOrderDiscountBenefit',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=(ecommerce.extensions.offer.mixins.BenefitWithoutRangeMixin, ecommerce.extensions.offer.mixins.PercentageBenefitMixin, 'offer.percentagediscountbenefit'),
        ),
        migrations.CreateModel(
            name='ManualEnrollmentOrderDiscountCondition',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=(ecommerce.extensions.offer.mixins.ConditionWithoutRangeMixin, ecommerce.extensions.offer.mixins.SingleItemConsumptionConditionMixin, 'offer.condition'),
        ),
    ]