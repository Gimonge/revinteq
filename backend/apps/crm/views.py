"""Revinteq CRM API Views"""
import logging
from rest_framework.views import APIView
from rest_framework.authentication import BaseAuthentication
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CRMUser, CRMLead, CRMContact, CRMActivity
from .permissions import IsCRMUser

logger = logging.getLogger(__name__)

class NoAuthentication(BaseAuthentication):
    """Skip standard JWT auth — CRM uses its own token validation via IsCRMUser permission."""
    def authenticate(self, request):
        return None

class NoAuthentication(BaseAuthentication):
    """Skip standard JWT auth — CRM uses its own token validation via IsCRMUser permission."""
    def authenticate(self, request):
        return None


class CRMLoginView(APIView):
    authentication_classes = [NoAuthentication]
    permission_classes = [AllowAny]
    def post(self, request):
        email    = request.data.get("email","").strip().lower()
        password = request.data.get("password","")
        if not email or not password:
            return Response({"error":True,"message":"Email and password required."},status=400)
        try:
            user_obj = CRMUser.objects.get(email=email)
            if not user_obj.check_password(password):
                return Response({"error":True,"message":"Invalid credentials."},status=401)
            if not user_obj.is_active:
                return Response({"error":True,"message":"Account disabled."},status=401)
        except CRMUser.DoesNotExist:
            return Response({"error":True,"message":"Invalid credentials."},status=401)
        refresh = RefreshToken()
        refresh["crm_user_id"]    = str(user_obj.id)
        refresh["crm_user_email"] = user_obj.email
        return Response({
            "access":str(refresh.access_token),"refresh":str(refresh),
            "user":{"id":str(user_obj.id),"email":user_obj.email,"name":user_obj.name,"role":user_obj.role}
        })


class CRMRefreshView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            return Response({"error":True,"message":"Refresh token required."},status=400)
        try:
            refresh = RefreshToken(token)
            return Response({"access":str(refresh.access_token)})
        except Exception:
            return Response({"error":True,"message":"Invalid token."},status=401)


class CRMMeView(APIView):
    authentication_classes = [NoAuthentication]
    permission_classes = [IsCRMUser]
    def get(self, request):
        u = request.crm_user
        return Response({"id":str(u.id),"email":u.email,"name":u.name,"role":u.role})


class CRMDashboardView(APIView):
    authentication_classes = [NoAuthentication]
    permission_classes = [IsCRMUser]
    def get(self, request):
        from django.db.models import Count, Sum
        from django.utils import timezone
        now = timezone.now()
        month_start = now.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
        leads = CRMLead.objects.all()
        by_status = {s:0 for s,_ in CRMLead.STATUS}
        for row in leads.values("status").annotate(n=Count("id")):
            by_status[row["status"]] = row["n"]
        pipeline_value = leads.filter(
            status__in=["new","contacted","proposal","negotiation"]
        ).aggregate(v=Sum("estimated_value"))["v"] or 0
        won_value = leads.filter(status="won",won_at__gte=month_start).aggregate(v=Sum("estimated_value"))["v"] or 0
        today_end = now.replace(hour=23,minute=59,second=59)
        due_today = CRMActivity.objects.filter(completed=False,due_date__lte=today_end).count()
        recent = CRMActivity.objects.select_related("lead").order_by("-created_at")[:5]
        return Response({
            "pipeline":{"new":by_status.get("new",0),"contacted":by_status.get("contacted",0),
                "proposal":by_status.get("proposal",0),"negotiation":by_status.get("negotiation",0),
                "won":by_status.get("won",0),"lost":by_status.get("lost",0),"total":leads.count()},
            "pipeline_value":float(pipeline_value),"won_this_month":float(won_value),
            "due_today":due_today,
            "recent_activities":[{"id":str(a.id),"type":a.type,"subject":a.subject,
                "lead":a.lead.company_name,"created":a.created_at.isoformat()} for a in recent],
        })


class CRMLeadListView(APIView):
    authentication_classes = [NoAuthentication]
    permission_classes = [IsCRMUser]
    def get(self, request):
        from django.db.models import Q
        qs = CRMLead.objects.select_related("contact","assigned_to").all()
        if request.query_params.get("status"):   qs=qs.filter(status=request.query_params["status"])
        if request.query_params.get("source"):   qs=qs.filter(source=request.query_params["source"])
        if request.query_params.get("industry"): qs=qs.filter(industry=request.query_params["industry"])
        if request.query_params.get("search"):
            q=request.query_params["search"]
            qs=qs.filter(Q(company_name__icontains=q)|Q(location__icontains=q)|Q(notes__icontains=q))
        data=[]
        for l in qs:
            data.append({"id":str(l.id),"company_name":l.company_name,"industry":l.industry,
                "source":l.source,"status":l.status,"website":l.website,"instagram":l.instagram,
                "facebook":l.facebook,"location":l.location,
                "monthly_ad_spend":float(l.monthly_ad_spend) if l.monthly_ad_spend else None,
                "estimated_value":float(l.estimated_value) if l.estimated_value else None,
                "probability":l.probability,"notes":l.notes,"lost_reason":l.lost_reason,
                "contact":{"id":str(l.contact.id),"name":l.contact.name,"phone":l.contact.phone} if l.contact else None,
                "assigned_to":{"id":str(l.assigned_to.id),"name":l.assigned_to.name} if l.assigned_to else None,
                "created_at":l.created_at.isoformat(),"updated_at":l.updated_at.isoformat(),
                "activity_count":l.activities.count()})
        return Response(data)

    def post(self, request):
        d=request.data
        lead=CRMLead.objects.create(
            company_name=d.get("company_name",""),industry=d.get("industry","digital_marketing"),
            source=d.get("source","manual"),status=d.get("status","new"),
            website=d.get("website",""),instagram=d.get("instagram",""),facebook=d.get("facebook",""),
            location=d.get("location","Nairobi"),monthly_ad_spend=d.get("monthly_ad_spend") or None,
            estimated_value=d.get("estimated_value") or None,probability=d.get("probability",20),
            notes=d.get("notes",""),
        )
        return Response({"id":str(lead.id),"company_name":lead.company_name},status=201)


class CRMLeadDetailView(APIView):
    authentication_classes = [NoAuthentication]
    permission_classes = [IsCRMUser]
    def _get(self, lead_id):
        try: return CRMLead.objects.select_related("contact","assigned_to").get(id=lead_id)
        except CRMLead.DoesNotExist: return None

    def get(self, request, lead_id):
        lead=self._get(lead_id)
        if not lead: return Response({"error":"Not found."},status=404)
        activities=lead.activities.select_related("created_by").order_by("-created_at")
        return Response({"id":str(lead.id),"company_name":lead.company_name,"industry":lead.industry,
            "source":lead.source,"status":lead.status,"website":lead.website,"instagram":lead.instagram,
            "facebook":lead.facebook,"location":lead.location,
            "monthly_ad_spend":float(lead.monthly_ad_spend) if lead.monthly_ad_spend else None,
            "estimated_value":float(lead.estimated_value) if lead.estimated_value else None,
            "probability":lead.probability,"notes":lead.notes,"lost_reason":lead.lost_reason,
            "contact":{"id":str(lead.contact.id),"name":lead.contact.name,"phone":lead.contact.phone,"email":lead.contact.email} if lead.contact else None,
            "assigned_to":{"id":str(lead.assigned_to.id),"name":lead.assigned_to.name} if lead.assigned_to else None,
            "created_at":lead.created_at.isoformat(),"updated_at":lead.updated_at.isoformat(),
            "activities":[{"id":str(a.id),"type":a.type,"subject":a.subject,"notes":a.notes,
                "outcome":a.outcome,"due_date":a.due_date.isoformat() if a.due_date else None,
                "completed":a.completed,"created_by":a.created_by.name if a.created_by else "",
                "created_at":a.created_at.isoformat()} for a in activities]})

    def patch(self, request, lead_id):
        lead=self._get(lead_id)
        if not lead: return Response({"error":"Not found."},status=404)
        d=request.data
        for f in ["company_name","industry","source","status","website","instagram","facebook","location","notes","lost_reason","probability"]:
            if f in d: setattr(lead,f,d[f])
        if "monthly_ad_spend" in d: lead.monthly_ad_spend=d["monthly_ad_spend"] or None
        if "estimated_value"  in d: lead.estimated_value=d["estimated_value"] or None
        lead.save()
        return Response({"id":str(lead.id),"status":lead.status})

    def delete(self, request, lead_id):
        lead=self._get(lead_id)
        if not lead: return Response({"error":"Not found."},status=404)
        lead.delete()
        return Response({"deleted":True})


class CRMActivityView(APIView):
    authentication_classes = [NoAuthentication]
    permission_classes = [IsCRMUser]
    def post(self, request, lead_id):
        try: lead=CRMLead.objects.get(id=lead_id)
        except CRMLead.DoesNotExist: return Response({"error":"Lead not found."},status=404)
        d=request.data
        a=CRMActivity.objects.create(lead=lead,type=d.get("type","note"),subject=d.get("subject",""),
            notes=d.get("notes",""),outcome=d.get("outcome",""),due_date=d.get("due_date") or None,
            completed=d.get("completed",False),created_by=request.crm_user)
        return Response({"id":str(a.id)},status=201)

    def patch(self, request, lead_id, activity_id):
        try: activity=CRMActivity.objects.get(id=activity_id)
        except CRMActivity.DoesNotExist: return Response({"error":"Not found."},status=404)
        d=request.data
        for f in ["subject","notes","outcome","completed"]:
            if f in d: setattr(activity,f,d[f])
        if d.get("completed") and not activity.completed_at:
            from django.utils import timezone
            activity.completed_at=timezone.now()
        activity.save()
        return Response({"id":str(activity.id)})


class CRMContactListView(APIView):
    authentication_classes = [NoAuthentication]
    permission_classes = [IsCRMUser]
    def get(self, request):
        from django.db.models import Q
        qs=CRMContact.objects.all()
        if request.query_params.get("search"):
            s=request.query_params["search"]
            qs=qs.filter(Q(name__icontains=s)|Q(company_name__icontains=s)|Q(email__icontains=s))
        return Response([{"id":str(c.id),"name":c.name,"email":c.email,"phone":c.phone,
            "position":c.position,"company_name":c.company_name,"linkedin":c.linkedin,"notes":c.notes} for c in qs])

    def post(self, request):
        d=request.data
        c=CRMContact.objects.create(name=d.get("name",""),email=d.get("email",""),phone=d.get("phone",""),
            position=d.get("position",""),company_name=d.get("company_name",""),
            linkedin=d.get("linkedin",""),notes=d.get("notes",""))
        return Response({"id":str(c.id)},status=201)


class CRMUserListView(APIView):
    authentication_classes = [NoAuthentication]
    permission_classes = [IsCRMUser]
    def get(self, request):
        if request.crm_user.role != "admin":
            return Response({"error":"Admin only."},status=403)
        return Response([{"id":str(u.id),"email":u.email,"name":u.name,"role":u.role,"is_active":u.is_active}
            for u in CRMUser.objects.all()])

    def post(self, request):
        if request.crm_user.role != "admin":
            return Response({"error":"Admin only."},status=403)
        d=request.data
        if CRMUser.objects.filter(email=d.get("email","")).exists():
            return Response({"error":"Email already exists."},status=400)
        u=CRMUser.objects.create_user(email=d.get("email",""),password=d.get("password",""),
            name=d.get("name",""),role=d.get("role","sales"))
        return Response({"id":str(u.id)},status=201)


# ── Auto-create Customer when Lead is Won ─────────────────────

def auto_create_customer(lead):
    """Called when a lead status changes to 'won'"""
    from .models import CRMCustomer
    if hasattr(lead, 'customer'):
        return lead.customer  # Already exists
    contact = lead.contact
    customer = CRMCustomer.objects.create(
        lead         = lead,
        company_name = lead.company_name,
        contact_name = contact.name if contact else '',
        email        = contact.email if contact else '',
        phone        = contact.phone if contact else '',
        website      = lead.website or '',
        notes        = lead.notes or '',
    )
    return customer


# ── Customers ─────────────────────────────────────────────────

class CRMCustomerListView(APIView):
    authentication_classes = [NoAuthentication]
    permission_classes = [IsCRMUser]

    def get(self, request):
        from .models import CRMCustomer
        customers = CRMCustomer.objects.all()
        search = request.query_params.get('search')
        if search:
            from django.db.models import Q
            customers = customers.filter(
                Q(company_name__icontains=search)|Q(contact_name__icontains=search)|Q(email__icontains=search)
            )
        return Response([{
            'id':           str(c.id),
            'company_name': c.company_name,
            'contact_name': c.contact_name,
            'email':        c.email,
            'phone':        c.phone,
            'website':      c.website,
            'notes':        c.notes,
            'lead_id':      str(c.lead.id) if c.lead else None,
            'invoice_count': c.invoices.count(),
            'total_invoiced': float(sum(i.total for i in c.invoices.all())),
            'total_paid':     float(sum(i.amount_paid for i in c.invoices.all())),
            'created_at':   c.created_at.isoformat(),
        } for c in customers])

    def post(self, request):
        from .models import CRMCustomer
        d = request.data
        c = CRMCustomer.objects.create(
            company_name = d.get('company_name',''),
            contact_name = d.get('contact_name',''),
            email        = d.get('email',''),
            phone        = d.get('phone',''),
            address      = d.get('address',''),
            website      = d.get('website',''),
            notes        = d.get('notes',''),
        )
        return Response({'id': str(c.id)}, status=201)


# ── Invoices ──────────────────────────────────────────────────

class CRMInvoiceListView(APIView):
    authentication_classes = [NoAuthentication]
    permission_classes = [IsCRMUser]

    def get(self, request):
        from .models import CRMInvoice
        qs = CRMInvoice.objects.select_related('customer').prefetch_related('items','receipts').all()
        status = request.query_params.get('status')
        if status: qs = qs.filter(status=status)
        return Response([_invoice_data(inv) for inv in qs])

    def post(self, request):
        from .models import CRMInvoice, CRMInvoiceItem, CRMCustomer
        from django.utils import timezone
        d = request.data
        try:
            customer = CRMCustomer.objects.get(id=d.get('customer_id'))
        except CRMCustomer.DoesNotExist:
            return Response({'error': 'Customer not found.'}, status=404)

        inv = CRMInvoice(
            customer   = customer,
            issue_date = d.get('issue_date', timezone.now().date()),
            due_date   = d.get('due_date') or None,
            notes      = d.get('notes',''),
            terms      = d.get('terms','Payment due within 30 days.'),
            tax_rate   = d.get('tax_rate', 16),
            status     = 'draft',
        )
        # Generate invoice number before save
        year  = timezone.now().year
        count = CRMInvoice.objects.filter(created_at__year=year).count() + 1
        inv.invoice_no = f"INV-{year}-{count:04d}"
        inv.save()

        # Create items
        subtotal = 0
        for item in d.get('items', []):
            qty   = float(item.get('quantity', 1))
            price = float(item.get('unit_price', 0))
            amt   = round(qty * price, 2)
            CRMInvoiceItem.objects.create(
                invoice     = inv,
                description = item.get('description',''),
                quantity    = qty,
                unit_price  = price,
                amount      = amt,
            )
            subtotal += amt

        # Update totals
        tax_amount = round(subtotal * float(inv.tax_rate) / 100, 2)
        CRMInvoice.objects.filter(pk=inv.pk).update(
            subtotal=subtotal, tax_amount=tax_amount,
            total=subtotal+tax_amount
        )
        inv.refresh_from_db()
        return Response(_invoice_data(inv), status=201)


class CRMInvoiceDetailView(APIView):
    authentication_classes = [NoAuthentication]
    permission_classes = [IsCRMUser]

    def get(self, request, invoice_id):
        from .models import CRMInvoice
        try:
            inv = CRMInvoice.objects.select_related('customer').prefetch_related('items','receipts').get(id=invoice_id)
            return Response(_invoice_data(inv, detail=True))
        except CRMInvoice.DoesNotExist:
            return Response({'error': 'Not found.'}, status=404)

    def patch(self, request, invoice_id):
        from .models import CRMInvoice
        try:
            inv = CRMInvoice.objects.get(id=invoice_id)
        except CRMInvoice.DoesNotExist:
            return Response({'error': 'Not found.'}, status=404)
        d = request.data
        for field in ['status','notes','terms','due_date']:
            if field in d:
                setattr(inv, field, d[field])
        inv.save()
        return Response({'id': str(inv.id), 'status': inv.status})


def _invoice_data(inv, detail=False):
    data = {
        'id':           str(inv.id),
        'invoice_no':   inv.invoice_no,
        'status':       inv.status,
        'issue_date':   inv.issue_date.isoformat() if inv.issue_date else None,
        'due_date':     inv.due_date.isoformat() if inv.due_date else None,
        'notes':        inv.notes,
        'terms':        inv.terms,
        'subtotal':     float(inv.subtotal),
        'tax_rate':     float(inv.tax_rate),
        'tax_amount':   float(inv.tax_amount),
        'total':        float(inv.total),
        'amount_paid':  float(inv.amount_paid),
        'balance_due':  float(inv.total - inv.amount_paid),
        'customer': {
            'id':           str(inv.customer.id),
            'company_name': inv.customer.company_name,
            'contact_name': inv.customer.contact_name,
            'email':        inv.customer.email,
            'phone':        inv.customer.phone,
            'address':      inv.customer.address,
        },
        'items': [{
            'id':          str(i.id),
            'description': i.description,
            'quantity':    float(i.quantity),
            'unit_price':  float(i.unit_price),
            'amount':      float(i.amount),
        } for i in inv.items.all()],
        'created_at': inv.created_at.isoformat(),
    }
    if detail:
        data['receipts'] = [{
            'id':          str(r.id),
            'amount':      float(r.amount),
            'method':      r.method,
            'reference':   r.reference,
            'notes':       r.notes,
            'received_at': r.received_at.isoformat(),
        } for r in inv.receipts.all()]
    return data


# ── Receipts ──────────────────────────────────────────────────

class CRMReceiptView(APIView):
    authentication_classes = [NoAuthentication]
    permission_classes = [IsCRMUser]

    def post(self, request, invoice_id):
        from .models import CRMInvoice, CRMReceipt
        from django.utils import timezone
        try:
            inv = CRMInvoice.objects.get(id=invoice_id)
        except CRMInvoice.DoesNotExist:
            return Response({'error': 'Invoice not found.'}, status=404)

        d = request.data
        receipt = CRMReceipt.objects.create(
            invoice     = inv,
            amount      = d.get('amount', 0),
            method      = d.get('method', 'mpesa'),
            reference   = d.get('reference',''),
            notes       = d.get('notes',''),
            received_at = d.get('received_at', timezone.now().date()),
        )
        return Response({'id': str(receipt.id)}, status=201)


# ── Financial Summary ─────────────────────────────────────────

class CRMFinancialSummaryView(APIView):
    authentication_classes = [NoAuthentication]
    permission_classes = [IsCRMUser]

    def get(self, request):
        from .models import CRMInvoice
        from django.db.models import Sum, Count
        from django.utils import timezone

        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        invoices = CRMInvoice.objects.all()

        total_invoiced = float(invoices.aggregate(s=Sum('total'))['s'] or 0)
        total_paid     = float(invoices.aggregate(s=Sum('amount_paid'))['s'] or 0)
        total_pending  = total_invoiced - total_paid

        this_month = invoices.filter(created_at__gte=month_start)
        month_invoiced = float(this_month.aggregate(s=Sum('total'))['s'] or 0)
        month_paid     = float(this_month.aggregate(s=Sum('amount_paid'))['s'] or 0)

        by_status = {}
        for row in invoices.values('status').annotate(n=Count('id'), total=Sum('total')):
            by_status[row['status']] = {'count': row['n'], 'total': float(row['total'] or 0)}

        overdue = invoices.filter(
            status__in=['sent','partial'],
            due_date__lt=now.date()
        )

        return Response({
            'total_invoiced':  total_invoiced,
            'total_paid':      total_paid,
            'total_pending':   total_pending,
            'month_invoiced':  month_invoiced,
            'month_paid':      month_paid,
            'by_status':       by_status,
            'overdue_count':   overdue.count(),
            'overdue_amount':  float(sum(inv.total - inv.amount_paid for inv in overdue)),
            'invoice_count':   invoices.count(),
        })


# ── Google Places Lead Import ─────────────────────────────────

class CRMGooglePlacesSearchView(APIView):
    """
    POST /api/v1/crm/leads/import/google/
    Search Google Places for businesses and import as leads.
    """
    authentication_classes = [NoAuthentication]
    permission_classes = [IsCRMUser]

    def post(self, request):
        import requests
        from django.conf import settings

        query    = request.data.get('query', 'digital marketing agency Nairobi Kenya')
        location = request.data.get('location', 'Nairobi, Kenya')
        api_key  = getattr(settings, 'GOOGLE_PLACES_API_KEY', '')

        if not api_key:
            return Response({'error': 'Google Places API key not configured.'}, status=500)

        results = []
        next_page_token = None
        pages = 0

        while pages < 3:  # Max 3 pages = 60 results
            params = {
                'query':  f"{query} {location}",
                'key':    api_key,
                'type':   'establishment',
            }
            if next_page_token:
                params = {'pagetoken': next_page_token, 'key': api_key}

            try:
                resp = requests.get(
                    'https://maps.googleapis.com/maps/api/place/textsearch/json',
                    params=params, timeout=10
                )
                data = resp.json()
            except Exception as e:
                logger.error(f"Google Places error: {e}")
                break

            for place in data.get('results', []):
                # Get place details for phone and website
                details = self._get_details(place['place_id'], api_key)
                results.append({
                    'place_id':     place['place_id'],
                    'name':         place.get('name', ''),
                    'address':      place.get('formatted_address', ''),
                    'location':     self._extract_city(place.get('formatted_address', '')),
                    'rating':       place.get('rating'),
                    'phone':        details.get('phone', ''),
                    'website':      details.get('website', ''),
                    'maps_url':     f"https://maps.google.com/?cid={place.get('reference','')}",
                    'types':        place.get('types', []),
                    'already_imported': self._already_imported(place['place_id']),
                })

            next_page_token = data.get('next_page_token')
            pages += 1
            if not next_page_token:
                break

            import time
            time.sleep(2)  # Required delay for next_page_token

        return Response({
            'results': results,
            'total':   len(results),
            'query':   query,
            'location': location,
        })

    def _get_details(self, place_id, api_key):
        import requests
        try:
            resp = requests.get(
                'https://maps.googleapis.com/maps/api/place/details/json',
                params={
                    'place_id': place_id,
                    'fields':   'formatted_phone_number,website',
                    'key':      api_key,
                },
                timeout=5
            )
            result = resp.json().get('result', {})
            return {
                'phone':   result.get('formatted_phone_number', ''),
                'website': result.get('website', ''),
            }
        except Exception:
            return {}

    def _extract_city(self, address):
        """Extract city from formatted address"""
        if not address:
            return 'Kenya'
        parts = address.split(',')
        if len(parts) >= 2:
            return parts[-3].strip() if len(parts) >= 3 else parts[-2].strip()
        return 'Kenya'

    def _already_imported(self, place_id):
        """Check if this place was already imported as a lead"""
        from .models import CRMLead
        return CRMLead.objects.filter(notes__icontains=place_id).exists()


class CRMImportLeadsView(APIView):
    """
    POST /api/v1/crm/leads/import/
    Bulk import selected places as leads with contacts.
    """
    authentication_classes = [NoAuthentication]
    permission_classes = [IsCRMUser]

    def post(self, request):
        from .models import CRMLead, CRMContact
        places   = request.data.get('places', [])
        source   = request.data.get('source', 'google_maps')
        industry = request.data.get('industry', 'digital_marketing')
        imported = 0
        skipped  = 0

        for place in places:
            # Skip already imported
            if place.get('already_imported'):
                skipped += 1
                continue

            # Create contact if phone exists
            contact = None
            if place.get('phone'):
                contact = CRMContact.objects.create(
                    name         = place.get('name', ''),
                    company_name = place.get('name', ''),
                    phone        = place.get('phone', ''),
                )

            # Create lead
            CRMLead.objects.create(
                company_name = place.get('name', ''),
                industry     = industry,
                source       = source,
                status       = 'new',
                website      = place.get('website', ''),
                location     = place.get('location', 'Kenya'),
                contact      = contact,
                notes        = f"Imported from Google Maps. Place ID: {place.get('place_id','')}. Address: {place.get('address','')}. Rating: {place.get('rating','')}",
            )
            imported += 1

        return Response({
            'imported': imported,
            'skipped':  skipped,
            'total':    len(places),
        })
