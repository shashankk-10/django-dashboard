from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, F, Count
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from datetime import timedelta
import logging

from .models import Instrument, Position, Trade, MarketData
from .serializers import *
from django.db import models

logger = logging.getLogger(__name__)

class PositionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PositionSerializer
    
    def get_queryset(self):
        return Position.objects.select_related('instrument').exclude(
            quantity=0
        ).order_by('-last_updated')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Portfolio summary with caching"""
        cache_key = 'portfolio_summary'
        summary = cache.get(cache_key)
        
        if summary is None:
            with transaction.atomic():
                positions = self.get_queryset()
                
                # Database aggregation for performance
                aggregates = positions.aggregate(
                    total_positions=Count('id'),
                    total_market_value=Sum(F('quantity') * F('current_price')),
                    total_cost_basis=Sum(F('quantity') * F('avg_cost'))
                )
                
                total_market_value = float(aggregates['total_market_value'] or 0)
                total_cost_basis = float(aggregates['total_cost_basis'] or 0)
                total_pnl = total_market_value - total_cost_basis
                
                summary = {
                    'total_positions': aggregates['total_positions'],
                    'total_market_value': total_market_value,
                    'total_pnl': total_pnl,
                    'total_pnl_percentage': (total_pnl / total_cost_basis * 100) if total_cost_basis else 0,
                    'last_updated': timezone.now().isoformat()
                }
                
                # Cache for 30 seconds
                cache.set(cache_key, summary, 30)
                logger.info(f"Portfolio summary calculated: {summary}")
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def top_performers(self, request):
        """Top 5 performing positions"""
        positions = self.get_queryset()[:20]  # Limit for performance
        
        position_performance = []
        for pos in positions:
            position_performance.append({
                'symbol': pos.instrument.symbol,
                'pnl_percentage': float(pos.pnl_percentage),
                'unrealized_pnl': float(pos.unrealized_pnl),
                'market_value': float(pos.market_value)
            })
        
        position_performance.sort(key=lambda x: x['pnl_percentage'], reverse=True)
        return Response(position_performance[:5])

class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TradeSerializer
    
    def get_queryset(self):
        queryset = Trade.objects.select_related('instrument').order_by('-timestamp')
        
        # Date filtering
        days = self.request.query_params.get('days', 7)
        if days:
            cutoff = timezone.now() - timedelta(days=int(days))
            queryset = queryset.filter(timestamp__gte=cutoff)
        
        return queryset[:500]  # Limit results

class MarketDataViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MarketDataSerializer
    
    def get_queryset(self):
        # Latest market data per instrument
        latest_ids = MarketData.objects.values('instrument').annotate(
            latest_id=models.Max('id')
        ).values_list('latest_id', flat=True)
        
        return MarketData.objects.filter(
            id__in=latest_ids
        ).select_related('instrument')

class InstrumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        instrument_type = self.request.query_params.get('type')
        if instrument_type:
            queryset = queryset.filter(instrument_type=instrument_type.upper())
        
        return queryset.order_by('symbol')
