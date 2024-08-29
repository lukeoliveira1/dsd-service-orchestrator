# orchestrator/urls.py
from django.urls import path
from .views import PurchaseProductView

urlpatterns = [
    path('purchase/', PurchaseProductView.as_view(), name='purchase-product'),
]
