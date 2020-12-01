# -*- coding: utf-8 -*-
import datetime
import logging
import random
import json
import threading
from pytz import UTC

from decimal import Decimal
from urlparse import urljoin
from django.urls import reverse
from oscar.core.loading import get_model
from ecommerce.core.url_utils import get_ecommerce_url
from ecommerce.extensions.payment.processors import BasePaymentProcessor, HandledProcessorResponse
from ecommerce.courses.utils import get_course_info_from_catalog

from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest
from alipay.aop.api.util.SignatureUtils import verify_with_rsa

PaymentProcessorResponse = get_model('payment', 'PaymentProcessorResponse')

logger = logging.getLogger(__name__)


class AliPay(BasePaymentProcessor):

    NAME = 'alipay'
    DEFAULT_PROFILE_NAME = 'default'

    def __init__(self, site):
        super(AliPay, self).__init__(site)

        alipay_conf = AlipayClientConfig()
        alipay_conf.app_id = int(self.configuration['app_id'])
        mode = self.configuration['mode'].decode('utf-8')
        if mode == 'sandbox':
            alipay_conf.server_url = 'https://openapi.alipaydev.com/gateway.do'
        else:
            alipay_conf.server_url = 'https://openapi.alipay.com/gateway.do'
        alipay_conf.app_private_key = open(self.configuration['app_private_key_path']).read()
        alipay_conf.alipay_public_key = open(self.configuration['alipay_public_key_path']).read()
        self.alipay_conf = alipay_conf
        self.alipay_client = DefaultAlipayClient(alipay_client_config=alipay_conf, logger=logger)

        self.Debug = False if self.configuration['mode'] is 'sandbox' else True

    def get_parameters(self, trade_id, body, subject, total_amount):
        alipay_model = AlipayTradePagePayModel()
        alipay_model.out_trade_no = trade_id
        alipay_model.total_amount = total_amount
        alipay_model.product_code = b"FAST_INSTANT_TRADE_PAY"
        alipay_model.subject = subject
        alipay_model.body = body

        alipay_request = AlipayTradePagePayRequest(biz_model=alipay_model)
        alipay_request.notify_url = str(urljoin(get_ecommerce_url(), reverse('alipay:notify')))
        alipay_request.return_url = str(urljoin(get_ecommerce_url(), reverse('alipay:return')))
        pay_url = self.alipay_client.page_execute(alipay_request, http_method="GET")

        parameters = alipay_model.to_alipay_dict()
        parameters['payment_page_url'] = pay_url

        return parameters

    @property
    def cancel_url(self):
        return get_ecommerce_url(self.configuration['cancel_checkout_path'])

    @property
    def error_url(self):
        return get_ecommerce_url(self.configuration['error_path'])

    @staticmethod
    def create_trade_id(bid):
        cur_datetime = datetime.datetime.now(UTC).strftime('%Y%m%d%H%M%S')
        rand_num = random.randint(1000, 9999)
        mch_vno = cur_datetime + str(rand_num) + str(bid)
        return mch_vno

    @staticmethod
    def str_to_specify_digits(feestr, digits_length=2):
        try:
            digits_str = '0.{digits}'.format(digits=digits_length * '0')
            result_str = Decimal(feestr).quantize(Decimal(digits_str))
            return str(result_str)
        except Exception as ex:
            return feestr

    def get_transaction_parameters(self, basket, request=None, use_client_side_checkout=False, **kwargs):
        """
        approval_url
        """
        trade_id = self.create_trade_id(basket.id)
        try:
            course_data = get_course_info_from_catalog(request.site, basket.all_lines()[0].product)
            subject = body = course_data.get('title')
        except Exception, e:
            logger.exception(e)
            subject = body = b'buy course'
        total_amount = self.str_to_specify_digits(str(basket.total_incl_tax))

        parameters = self.get_parameters(trade_id, body, subject, total_amount)
        if not PaymentProcessorResponse.objects.filter(processor_name=self.NAME, basket=basket).update(transaction_id=trade_id):
            self.record_processor_response({}, transaction_id=trade_id, basket=basket)

        return parameters

    def handle_processor_response(self, response, basket=None):
        sign = response.pop("sign", None)
        response.pop('sign_type')
        response_dict = sorted(response.items(), key=lambda x: x[0], reverse=False)
        message = "&".join(u"{}={}".format(k, v) for k, v in response_dict).encode()
        try:
            verify_res = verify_with_rsa(self.alipay_conf.alipay_public_key, message, sign)
        except Exception as e:
            raise Exception('Response sign verify failed. ' + str(e))
        if not verify_res:
            raise Exception('Response sign verify failed. ')

        transaction_id = response.get('out_trade_no')
        PaymentProcessorResponse.objects.filter(
            processor_name=self.NAME,
            transaction_id=transaction_id
        ).update(response=response, basket=basket)

        total = Decimal(response.get('total_amount'))
        buyer_user_name = response.get('buyer_user_name')
        label = 'AliPay ({})'.format(buyer_user_name) if buyer_user_name else 'AliPay Account'
        return HandledProcessorResponse(
            transaction_id=transaction_id,
            total=total,
            currency='CNY',
            card_number=label,
            card_type=None
        )

    def issue_credit(self, order_number, basket, reference_number, amount, currency):
        pass
