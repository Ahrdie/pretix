from django.views.generic import ListView

from pretix.base.models import Item, WaitingListEntry


class WaitingListView(ListView):
    model = WaitingListEntry
    context_object_name = 'entries'
    paginate_by = 30
    template_name = 'pretixcontrol/waitinglist/index.html'
    permission = 'can_view_orders'

    def get_queryset(self):
        qs = WaitingListEntry.objects.filter(
            event=self.request.event
        ).select_related('item', 'variation', 'voucher')

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
        return ctx
