from django.contrib import admin
from django.template.response import TemplateResponse
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SyncLog


def commands_view(request):
    context = admin.site.each_context(request)
    context['title'] = 'Cloud Run Commands'
    return TemplateResponse(request, 'admin/commands.html', context)


# Sources that use address_label to store a state code
_STATE_SCOPED_SOURCES = {'openelections', 'openstates'}

_COMPLETED_STATUSES = [SyncLog.Status.COMPLETED, SyncLog.Status.COMPLETED_WITH_WARNINGS]


class CoverageSyncStatusView(APIView):
    """
    Public endpoint returning the most recent completed SyncLog entry per
    (source, address_label) pair.

    Response shape:
      {
        "as_of": "<ISO timestamp>",
        "global": {
          "civic_api": { last_completed_at, status, records_created, records_updated, records_skipped },
          "fec": { ... },
          ...
        },
        "by_state": {
          "WV": {
            "openelections": { ... },
            "openstates": { ... }
          },
          ...
        }
      }
    """

    permission_classes = [AllowAny]

    def get(self, request):
        # One row per (source, address_label) — latest completed only.
        # distinct('source', 'address_label') requires PostgreSQL.
        latest = (
            SyncLog.objects
            .filter(status__in=_COMPLETED_STATUSES, completed_at__isnull=False)
            .order_by('source', 'address_label', '-completed_at')
            .distinct('source', 'address_label')
        )

        global_sources: dict = {}
        by_state: dict = {}

        for log in latest:
            entry = {
                'last_completed_at': log.completed_at,
                'status': log.status,
                'records_created': log.records_created,
                'records_updated': log.records_updated,
                'records_skipped': log.records_skipped,
            }
            state = (log.address_label or '').upper()
            if log.source in _STATE_SCOPED_SOURCES and state:
                by_state.setdefault(state, {})[log.source] = entry
            else:
                global_sources[log.source] = entry

        return Response({
            'as_of': timezone.now(),
            'global': global_sources,
            'by_state': by_state,
        })
