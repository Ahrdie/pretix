from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView

from pretix.base.models import Item, WaitingListEntry
from pretix.base.models.waitinglist import WaitingListException


class WaitingListView(ListView):
    model = WaitingListEntry
    context_object_name = 'entries'
    paginate_by = 30
    template_name = 'pretixcontrol/waitinglist/index.html'
    permission = 'can_view_orders'

    def post(self, request, *args, **kwargs):
        if 'assign' in request.POST:
            try:
                wle = WaitingListEntry.objects.get(
                    pk=request.POST.get('assign'), event=self.request.event,
                )
                try:
                    wle.send_voucher()
                except WaitingListException as e:
                    messages.error(request, str(e))
                else:
                    messages.success(request, _('An email containing a voucher code has been sent to the '
                                                'specified address.'))
                return redirect(reverse('control:event.orders.waitinglist', kwargs={
                    'event': request.event.slug,
                    'organizer': request.event.organizer.slug
                }))
            except WaitingListEntry.DoesNotExist:
                messages.error(request, _('Waiting list entry not found.'))
                return redirect(reverse('control:event.orders.waitinglist', kwargs={
                    'event': request.event.slug,
                    'organizer': request.event.organizer.slug
                }))

    def get_queryset(self):
        qs = WaitingListEntry.objects.filter(
            event=self.request.event
        ).select_related('item', 'variation', 'voucher').prefetch_related('item__quotas', 'variation__quotas')

        s = self.request.GET.get("status", "")
        if s == 's':
            qs = qs.filter(voucher__isnull=False)
        elif s == 'a':
            pass
        else:
            qs = qs.filter(voucher__isnull=True)

        if self.request.GET.get("item", "") != "":
            i = self.request.GET.get("item", "")
            qs = qs.filter(item_id__in=(i,))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['items'] = Item.objects.filter(event=self.request.event)
        ctx['filtered'] = ("status" in self.request.GET or "item" in self.request.GET)

        itemvar_cache = {}
        quota_cache = {}
        for wle in ctx[self.context_object_name]:
            if (wle.item, wle.variation) in itemvar_cache:
                wle.availability = itemvar_cache.get((wle.item, wle.variation))
            else:
                wle.availability = (
                    wle.variation.check_quotas(count_waitinglist=False, _cache=quota_cache)
                    if wle.variation
                    else wle.item.check_quotas(count_waitinglist=False, _cache=quota_cache)
                )
                itemvar_cache[(wle.item, wle.variation)] = wle.availability

        return ctx
