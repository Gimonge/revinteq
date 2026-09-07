from django.urls import path
from .views import BulkUploadTemplateView, BulkUploadView, BulkUploadConfirmView

urlpatterns = [
    path('template/',                       BulkUploadTemplateView.as_view(), name='bulk-template'),
    path('upload/',                         BulkUploadView.as_view(),         name='bulk-upload'),
    path('<uuid:upload_id>/confirm/',       BulkUploadConfirmView.as_view(),  name='bulk-confirm'),
]
