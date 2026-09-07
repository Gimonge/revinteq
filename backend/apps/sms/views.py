"""Revinteq v3 — SMS Views"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.common.views import get_tenant
from rest_framework.permissions import IsAuthenticated
from apps.tenants.permissions import IsClientOrAdmin, IsAdminOrSuperAdmin
from .models import SMSConfig, SMSMessage, SMSTrigger
import logging

logger = logging.getLogger(__name__)


class SendSMSView(APIView):
    """
    POST /api/v1/sms/send/
    Manual SMS send — client selects recipients and message.
    """
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def post(self, request):
        recipients = request.data.get('recipients', [])
        message = request.data.get('message', '').strip()

        if not recipients:
            return Response(
                {'error': True, 'message': 'At least one recipient is required.'},
                status=400
            )
        if not message:
            return Response(
                {'error': True, 'message': 'Message cannot be empty.'},
                status=400
            )
        if len(message) > 160:
            return Response(
                {'error': True, 'message': 'Message exceeds 160 characters.'},
                status=400
            )

        try:
            sms_config = SMSConfig.objects.get(
                tenant=get_tenant(request), is_active=True
            )
        except SMSConfig.DoesNotExist:
            return Response(
                {'error': True, 'message': 'SMS is not configured for your account. Contact support.'},
                status=400
            )

        from .services.africastalking import ATSMSService
        service = ATSMSService(sms_config)

        # Bulk or single
        if isinstance(recipients, list) and len(recipients) > 1:
            logs = service.send_bulk(
                recipients=recipients,
                message=message,
                tenant=get_tenant(request),
                sent_by=request.user,
            )
            sent = sum(1 for l in logs if l.status == 'sent')
            failed = sum(1 for l in logs if l.status == 'failed')
            return Response({
                'message': f'Bulk SMS sent: {sent} delivered, {failed} failed.',
                'sent': sent, 'failed': failed,
            })
        else:
            phone = recipients[0] if isinstance(recipients, list) else recipients
            log = service.send(
                recipient=phone if isinstance(phone, str) else phone.get('phone', ''),
                message=message,
                tenant=get_tenant(request),
                source='manual',
                sent_by=request.user,
            )
            return Response({
                'message': 'SMS sent.' if log.status == 'sent' else 'SMS failed.',
                'status': log.status,
                'message_id': str(log.id),
            })


class SMSHistoryView(APIView):
    """GET /api/v1/sms/history/"""
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get(self, request):
        messages = SMSMessage.objects.filter(
            tenant=get_tenant(request)
        ).order_by('-created_at')[:200]

        return Response([{
            'id': str(m.id),
            'recipient': m.recipient_number,
            'recipient_name': m.recipient_name,
            'message': m.message,
            'status': m.status,
            'source': m.source,
            'trigger': m.trigger,
            'cost': m.cost,
            'sent_at': m.sent_at,
            'created_at': m.created_at,
        } for m in messages])


class SMSTriggerListView(APIView):
    """
    GET  /api/v1/sms/triggers/   — list auto-triggers
    POST /api/v1/sms/triggers/   — create/update trigger
    """
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get(self, request):
        triggers = SMSTrigger.objects.filter(tenant=get_tenant(request))
        return Response([{
            'id': str(t.id),
            'trigger': t.trigger,
            'trigger_display': t.get_trigger_display(),
            'message_template': t.message_template,
            'is_active': t.is_active,
        } for t in triggers])

    def post(self, request):
        trigger_key = request.data.get('trigger')
        template = request.data.get('message_template', '').strip()
        is_active = request.data.get('is_active', True)

        if not trigger_key or not template:
            return Response(
                {'error': True, 'message': 'trigger and message_template are required.'},
                status=400
            )

        trigger, created = SMSTrigger.objects.update_or_create(
            tenant=get_tenant(request),
            trigger=trigger_key,
            defaults={
                'message_template': template,
                'is_active': is_active,
            }
        )
        return Response({
            'message': f'Trigger {"created" if created else "updated"}.',
            'id': str(trigger.id),
        }, status=201 if created else 200)


class SMSConfigAdminView(APIView):
    """
    POST /api/v1/admin/sms-config/<tenant_id>/
    Admin configures Africa's Talking for a tenant.
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def post(self, request, tenant_id):
        from apps.tenants.models import Tenant
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Response({'error': True, 'message': 'Tenant not found.'}, status=404)

        data = request.data
        config, created = SMSConfig.objects.update_or_create(
            tenant=tenant,
            defaults={
                'api_key': data.get('api_key', ''),
                'username': data.get('username', ''),
                'sender_id': data.get('sender_id', ''),
                'is_active': True,
            }
        )
        return Response({
            'message': f'SMS config {"created" if created else "updated"} for {tenant.name}.',
            'username': config.username,
            'sender_id': config.sender_id,
        })


class SMSConfigView(APIView):
    """GET /api/v1/sms/config/ — get SMS config for current tenant"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.common.views import get_tenant
        from .models import SMSConfig
        tenant = get_tenant(request)
        if not tenant:
            return Response({'configured': False})
        try:
            config = SMSConfig.objects.get(tenant=tenant)
            return Response({
                'configured':     True,
                'is_active':      config.is_active,
                'username':       config.username,
                'sender_id':      config.sender_id or '',
                'credit_balance': str(config.credit_balance or '0.00'),
            })
        except Exception:
            return Response({'configured': False})


class SMSMessagesView(APIView):
    """GET /api/v1/sms/messages/ — list SMS messages for current tenant"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.common.views import get_tenant
        from .models import SMSMessage
        tenant = get_tenant(request)
        if not tenant:
            return Response([])
        msgs = SMSMessage.objects.filter(tenant=tenant).order_by('-created_at')[:100]
        data = []
        for m in msgs:
            data.append({
                'id':               str(m.id),
                'recipient_number': m.recipient_number,
                'message':          m.message,
                'status':           m.status,
                'source':           getattr(m, 'source', 'manual'),
                'cost':             str(getattr(m, 'cost', '0')),
                'created_at':       m.created_at.isoformat() if m.created_at else None,
            })
        return Response(data)
