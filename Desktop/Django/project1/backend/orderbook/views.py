from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework import generics, viewsets, status
from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache
from django.db.models import Q, Sum, Count, Avg, Max
from django.utils import timezone
import django_filters
from . models import Instrument, Order, Trade
from . serializers import (
    InstrumentSerializer, OrderSerializer, CreateOrderSerializer,
    OrderBookSerializer, TradeSerializer,
    OrderHistorySerializer, OrderStatsSerializer, InstrumentStatsSerializer
)

# Create your views here.
class InstrumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Instrument.objects.filter(is_active=True)
    serializer_class = InstrumentSerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ['symbol', 'name']

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        instrument = self.get_object()

        cache_key = f"instrument_stats_{instrument.id}"
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            return Response(cached_stats)

        orders_qs = Order.objects.filter(instrument=instrument)
        trades_qs = Trade.objects.filter(instrument=instrument)

        stats = {
            'order_count': orders_qs.count(),
            'active_orders': orders_qs.filter(status='ACTIVE').count(),
            'total_volume': orders_qs.aggregate(
                total=Sum('original_quantity')
            )['total'] or 0,
            'avg_price': orders_qs.aggregate(
                avg=Avg('price')
            )['avg'] or 0,
            'last_trade_price': trades_qs.order_by('-created_at').values_list(
                'price', flat=True
            ).first(),
            'last_trade_time': trades_qs.order_by('-created_at').values_list(
                'created_at', flat=True
            ).first(),
        }
        
        serialized_stats = InstrumentStatsSerializer({
            'instrument': instrument,
            **stats
        })

        cache.set(cache_key, serialized_stats.data, 30)

        return Response(serialized_stats.data)
    
class OrderFilter(django_filters.FilterSet):
    """Advanced filtering for orders"""
    instrument_symbol = django_filters.CharFilter(field_name='instrument__symbol', lookup_expr='iexact')
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    quantity_min = django_filters.NumberFilter(field_name='original_quantity', lookup_expr='gte')
    quantity_max = django_filters.NumberFilter(field_name='original_quantity', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Order
        fields = ['order_type', 'status']

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('instrument').all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = OrderFilter
    ordering_fields = ['created_at', 'price', 'original_quantity']
    ordering = ['-created_at']
    search_fields = ['instrument__symbol']

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateOrderSerializer
        elif self.action in ['list', 'history']:
            return OrderHistorySerializer
        return OrderSerializer

    def get_queryset(self):
        return Order.objects.select_related('instrument').prefetch_related(
            'buy_trade', 'sell_trade'
        )

    @action(detail=False, methods=['get'])
    def history(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        days = request.query_params.get('days')
        if days:
            try:
                days_int = int(days)
                start_date = timezone.now() - timezone.timedelta(days=days_int)
                queryset = queryset.filter(created_at__gte=start_date)
            except ValueError:
                pass

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        cache_key = "order_stats_global"
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            return Response(cached_stats)
        
        all_orders = Order.objects.all()
        
        stats = {
            'total_orders': all_orders.count(),
            'active_orders': all_orders.filter(status='ACTIVE').count(),
            'filled_orders': all_orders.filter(status='FILLED').count(),
            'partial_orders': all_orders.filter(status='PARTIAL').count(),
            'cancelled_orders': all_orders.filter(status='CANCELLED').count(),
            'total_volume': all_orders.aggregate(
                total=Sum('original_quantity')
            )['total'] or 0,
            'avg_order_size': all_orders.aggregate(
                avg=Avg('original_quantity')
            )['avg'] or 0,
            'instruments_count': all_orders.values('instrument').distinct().count(),
        }
        
        serialized_stats = OrderStatsSerializer(stats)
        
        cache.set(cache_key, serialized_stats.data, 60)
        
        return Response(serialized_stats.data)
    
    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        """Cancel a specific order"""
        order = self.get_object()
        
        if order.status != 'ACTIVE':
            return Response(
                {'error': 'Only active orders can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'CANCELLED'
        order.save()
        
        self._clear_order_caches(order)
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Override to clear caches on order creation"""
        order = serializer.save()
        self._clear_order_caches(order)
    
    def perform_update(self, serializer):
        """Override to clear caches on order update"""
        order = serializer.save()
        self._clear_order_caches(order)
    
    def _clear_order_caches(self, order):
        """Clear relevant caches when order changes"""
        cache.delete(f"orderbook_{order.instrument.id}")
        cache.delete(f"instrument_stats_{order.instrument.id}")
        cache.delete("order_stats_global")

class OrderBookAPIView(generics.RetrieveAPIView):
    """
    Real-time order book view for a specific instrument
    Heavily optimized with caching and efficient aggregation
    """
    permission_classes = [AllowAny]
    
    def get(self, request, instrument_id=None):
        """
        Get current order book for instrument
        """
        try:
            instrument = Instrument.objects.get(id=instrument_id, is_active=True)
        except Instrument.DoesNotExist:
            return Response(
                {'error': 'Instrument not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check cache first
        cache_key = f"orderbook_{instrument_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # Build order book from active orders
        active_orders = Order.objects.filter(
            instrument=instrument,
            status='ACTIVE',
            remaining_quantity__gt=0
        ).values('order_type', 'price').annotate(
            quantity=Sum('remaining_quantity'),
            order_count=Count('id')
        ).order_by('price')
        
        # Separate bids and asks
        bids = []
        asks = []
        
        for order in active_orders:
            order_data = {
                'price': order['price'],
                'quantity': order['quantity'],
                'order_count': order['order_count'],
                'order_type': order['order_type']
            }
            
            if order['order_type'] == 'BUY':
                bids.append(order_data)
            else:
                asks.append(order_data)
        
        # Sort bids (descending) and asks (ascending)
        bids.sort(key=lambda x: x['price'], reverse=True)
        asks.sort(key=lambda x: x['price'])
        
        # Take top 20 levels each side
        bids = bids[:20]
        asks = asks[:20]
        
        order_book_data = {
            'instrument': InstrumentSerializer(instrument).data,
            'bids': bids,
            'asks': asks,
            'last_updated': timezone.now()
        }
        
        serializer = OrderBookSerializer(order_book_data)
        
        # Cache for 5 seconds (very short for real-time data)
        cache.set(cache_key, serializer.data, 5)
        
        return Response(serializer.data)
    
class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only trade history
    """
    queryset = Trade.objects.select_related('instrument').all()
    serializer_class = TradeSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['instrument']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter trades by instrument if provided"""
        queryset = super().get_queryset()
        
        instrument_id = self.request.query_params.get('instrument_id')
        if instrument_id:
            queryset = queryset.filter(instrument_id=instrument_id)
            
        # Limit to recent trades for performance
        days = self.request.query_params.get('days', 7)
        try:
            days_int = int(days)
            start_date = timezone.now() - timezone.timedelta(days=days_int)
            queryset = queryset.filter(created_at__gte=start_date)
        except ValueError:
            pass
            
        return queryset

# Health check endpoint
class HealthCheckAPIView(generics.GenericAPIView):
    """Simple health check endpoint"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Return system health status"""
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now(),
            'version': '1.0.0'
        })