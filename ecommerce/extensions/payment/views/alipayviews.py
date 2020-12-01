import logging

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from django.db import transaction
from django.shortcuts import redirect
from django.utils import translation
from django.views.generic import View
from edx_rest_api_client.client import EdxRestApiClient
from oscar.apps.partner import strategy
from oscar.apps.payment.exceptions import PaymentError
from oscar.core.loading import get_model, get_class
from rest_framework.response import Response
from rest_framework.views import APIView

from ecommerce.core.url_utils import get_lms_url
from ecommerce.extensions.basket.utils import basket_add_organization_attribute
from ecommerce.extensions.checkout.mixins import EdxOrderPlacementMixin
from ecommerce.extensions.checkout.utils import get_receipt_page_url
from ecommerce.extensions.payment.processors.alipayprocessors import AliPay

logger = logging.getLogger(__name__)
Applicator = get_class('offer.applicator', 'Applicator')
NoShippingRequired = get_class('shipping.methods', 'NoShippingRequired')
OrderTotalCalculator = get_class('checkout.calculators', 'OrderTotalCalculator')
PaymentProcessorResponse = get_model('payment', 'PaymentProcessorResponse')

logger = logging.getLogger(__name__)


class AlipayPaymentNotifyView(EdxOrderPlacementMixin, APIView):

    @property
    def payment_processor(self):
        return AliPay(self.request.site)

    def _get_basket(self, payment_id):
        """
        Retrieve a basket using a payment ID.

        Arguments:
            payment_id: payment_id received from Alipay.

        Returns:

        """
        try:
            basket = PaymentProcessorResponse.objects.get(
                processor_name=self.payment_processor.NAME,
                transaction_id=payment_id
            ).basket
            basket.strategy = strategy.Default()
            Applicator().apply(basket, basket.owner, self.request)

            basket_add_organization_attribute(basket, self.request.GET)
            return basket
        except MultipleObjectsReturned:
            return None
        except Exception, e:
            logger.exception(e)
            return None

    def post(self, request):
        """Handle an incoming user returned to us by Alipay after approving payment."""
        if request.POST.get('sub_code'):
            return Response({'result': 'fail'})

        payment_id = request.POST.get('out_trade_no')
        basket = self._get_basket(payment_id)
        if not basket:
            return Response({'result': 'fail'})

        try:
            lms_api = EdxRestApiClient(get_lms_url('/api/user/v1/'),
                                       oauth_access_token=basket.owner.access_token,
                                       append_slash=False)
            user_lang = lms_api.preferences(basket.owner.username).get()
            translation.activate(user_lang.get('pref-lang', settings.LANGUAGE_CODE))
        except Exception, e:
            logger.exception(e)

        try:
            request.user = basket.owner
            with transaction.atomic():
                try:
                    self.handle_payment(request.POST.dict(), basket)
                except PaymentError:
                    return Response({'result': 'fail'})
        except:  # pylint: disable=bare-except
            logger.exception('Attempts to handle payment for basket [%d] failed.', basket.id)
            return Response({'result': 'fail'})

        self.call_handle_order_placement(basket, request)

        return Response({'result': 'success'})

    def call_handle_order_placement(self, basket, request):
        """
        place order
        """
        try:
            shipping_method = NoShippingRequired()
            shipping_charge = shipping_method.calculate(basket)
            order_total = OrderTotalCalculator().calculate(basket, shipping_charge)
            user = basket.owner
            # Given a basket, order number generation is idempotent. Although we've already
            # generated this order number once before, it's faster to generate it again
            # than to retrieve an invoice number from PayPal.
            order_number = basket.order_number

            order = self.handle_order_placement(
                order_number=order_number,
                user=user,
                basket=basket,
                shipping_address=None,
                shipping_method=shipping_method,
                shipping_charge=shipping_charge,
                billing_address=None,
                order_total=order_total,
                request=request
            )
            self.handle_post_order(order)
        except Exception as e:
            logger.exception(self.order_placement_failure_msg, basket.id, e)


class AlipayPaymentResultView(View):

    @property
    def payment_processor(self):
        return AliPay(self.request.site)

    def get(self, request):
        """
        """
        try:
            out_trade_no = request.GET.get('out_trade_no')
            basket = PaymentProcessorResponse.objects.get(transaction_id=out_trade_no).basket
            receipt_url = get_receipt_page_url(
                order_number=basket.order_number,
                site_configuration=basket.site.siteconfiguration
            )
            return redirect(receipt_url)
        except Exception, e:
            logger.exception(e)
        return redirect(self.payment_processor.error_url)
