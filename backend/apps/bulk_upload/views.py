"""
Revinteq v3 — Bulk Upload Views (RETIRED)
This whole feature let clients bulk-create Sale records from a
spreadsheet — same category as the manual Sales Logger and the
Pipeline board's inline sale-log, both retired for the same reason:
sales now come exclusively from the connected Kommo account (a deal
marked Won there syncs back automatically). Endpoints kept in place,
returning 410, so any old client code calling them gets a clear
explanation rather than a 404.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

RETIRED_MESSAGE = (
    'Bulk sales upload has been retired. Sales are now synced automatically '
    'from your connected Kommo account when a deal is marked Won — connect '
    'Kommo in Settings if you haven\'t already.'
)


class BulkUploadTemplateView(APIView):
    """GET /api/v1/bulk-upload/template/ — retired."""
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response({'error': True, 'message': RETIRED_MESSAGE}, status=410)


class BulkUploadView(APIView):
    """POST /api/v1/bulk-upload/upload/ — retired."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({'error': True, 'message': RETIRED_MESSAGE}, status=410)


class BulkUploadConfirmView(APIView):
    """POST /api/v1/bulk-upload/<upload_id>/confirm/ — retired."""
    permission_classes = [IsAuthenticated]

    def post(self, request, upload_id):
        return Response({'error': True, 'message': RETIRED_MESSAGE}, status=410)
