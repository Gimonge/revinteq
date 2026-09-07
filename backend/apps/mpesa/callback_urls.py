from django.urls import path
from .views import MPesaConfirmationView, MPesaValidationView
urlpatterns = [
    path('confirmation/<slug:tenant_slug>/', MPesaConfirmationView.as_view(), name='mpesa-confirm'),
    path('validation/<slug:tenant_slug>/',   MPesaValidationView.as_view(),   name='mpesa-validate'),
]
