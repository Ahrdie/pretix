import json
from collections import OrderedDict

from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _

from pretix.base.i18n import I18nFormField, I18nTextarea, LazyI18nString
from pretix.base.payment import BasePaymentProvider


class BankTransfer(BasePaymentProvider):
    identifier = 'banktransfer'
    verbose_name = _('Bank transfer')

    @property
    def settings_form_fields(self):
        form_field = I18nFormField(
            label=_('Bank account details'),
            widget=I18nTextarea,
        )
        return OrderedDict(
            list(super().settings_form_fields.items()) + [('bank_details', form_field)]
        )

    def payment_form_render(self, request) -> str:
        template = get_template('pretixplugins/banktransfer/checkout_payment_form.html')
        ctx = {
            'request': request,
            'event': self.event,
            'details': self.settings.get('bank_details', as_type=LazyI18nString),
        }
        return template.render(ctx)

    def checkout_prepare(self, request, total):
        return True

    def payment_is_valid_session(self, request):
        return True

    def checkout_confirm_render(self, request):
        return self.payment_form_render(request)

    def order_pending_mail_render(self, order) -> str:
        template = get_template('pretixplugins/banktransfer/email/order_pending.txt')
        ctx = {
            'event': self.event,
            'order': order,
            'details': self.settings.get('bank_details', as_type=LazyI18nString),
        }
        return template.render(ctx)

    def order_pending_render(self, request, order) -> str:
        template = get_template('pretixplugins/banktransfer/pending.html')
        ctx = {
            'event': self.event,
            'order': order,
            'details': self.settings.get('bank_details', as_type=LazyI18nString),
        }
        return template.render(ctx)

    def order_control_render(self, request, order) -> str:
        if order.payment_info:
            payment_info = json.loads(order.payment_info)
        else:
            payment_info = None
        template = get_template('pretixplugins/banktransfer/control.html')
        ctx = {'request': request, 'event': self.event,
               'payment_info': payment_info, 'order': order}
        return template.render(ctx)
