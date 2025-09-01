from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('positions', views.PositionViewSet, basename='position')
router.register('trades', views.TradeViewSet, basename='trade')
router.register('market-data', views.MarketDataViewSet, basename='marketdata')
router.register('instruments', views.InstrumentViewSet, basename='instrument')

urlpatterns = [
    path('', include(router.urls)),
]