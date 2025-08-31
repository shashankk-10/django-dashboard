from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'instruments', views.InstrumentViewSet, basename='instrument')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'trades', views.TradeViewSet, basename='trade')

urlpatterns = [
    path("", include(router.urls)),
    
    path("orderbook/<int:Pinstrument_id>/",
        views.OrderBookAPIView.as_view(), 
        name='orderbook-detail'),
    
    path("health/",
        views.HealthCheckAPIView.as_view(),
        name='health-check')
]