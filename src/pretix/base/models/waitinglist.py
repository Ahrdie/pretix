from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .base import LoggedModel
from .event import Event
from .items import Item, ItemVariation


class WaitingListEntry(LoggedModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="waitinglistentries",
        verbose_name=_("Event"),
    )
    created = models.DateTimeField(
        verbose_name=_("On waiting list since"),
        auto_now_add=True
    )
    email = models.EmailField(
        verbose_name=_("E-mail address")
    )
    voucher = models.ForeignKey(
        'Voucher',
        verbose_name=_("Assigned voucher"),
        null=True, blank=True
    )
    item = models.ForeignKey(
        Item, related_name='waitinglistentries',
        verbose_name=_("Product"),
        help_text=_(
            "The product the user waits for."
        )
    )
    variation = models.ForeignKey(
        ItemVariation, related_name='waitinglistentries',
        null=True, blank=True,
        verbose_name=_("Product variation"),
        help_text=_(
            "The variation of the product selected above."
        )
    )

    class Meta:
        verbose_name = _("Waiting list entry")
        verbose_name_plural = _("Waiting list entries")
        ordering = ['created']

    def __str__(self):
        return '%s waits for %s' % (str(self.email), str(self.item))

    def clean(self):
        if WaitingListEntry.objects.filter(
            item=self.item, variation=self.variation, email=self.email
        ).exclude(pk=self.pk).exists():
            raise ValidationError(_('You are already on this waiting list! We will notify '
                                    'you as soon as we have a ticket available for you.'))
        if not self.variation and self.item.has_variations:
            raise ValidationError(_('Please select a specific variation of this product.'))
