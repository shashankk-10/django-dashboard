from rest_framework import serializers
from django.utils import timezone
from .models import Instrument, Position, Trade, MarketData

class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = '__all__'

class PositionSerializer(serializers.ModelSerializer):
    # Calculated fields
    market_value = serializers.ReadOnlyField()
    unrealized_pnl = serializers.ReadOnlyField()
    pnl_percentage = serializers.ReadOnlyField()
    
    # Related fields
    instrument_symbol = serializers.CharField(source='instrument.symbol', read_only=True)
    instrument_name = serializers.CharField(source='instrument.name', read_only=True)
    instrument_type = serializers.CharField(source='instrument.instrument_type', read_only=True)
    
    # Data freshness
    age_seconds = serializers.SerializerMethodField()
    is_stale = serializers.SerializerMethodField()
    
    def get_age_seconds(self, obj):
        return int((timezone.now() - obj.last_updated).total_seconds())
    
    def get_is_stale(self, obj):
        return self.get_age_seconds(obj) > 60  # Stale if > 1 minute
    
    class Meta:
        model = Position
        fields = '__all__'

class TradeSerializer(serializers.ModelSerializer):
    instrument_symbol = serializers.CharField(source='instrument.symbol', read_only=True)
    instrument_name = serializers.CharField(source='instrument.name', read_only=True)
    
    class Meta:
        model = Trade
        fields = '__all__'

class MarketDataSerializer(serializers.ModelSerializer):
    spread = serializers.ReadOnlyField()
    spread_percentage = serializers.ReadOnlyField()
    instrument_symbol = serializers.CharField(source='instrument.symbol', read_only=True)
    
    class Meta:
        model = MarketData
        fields = '__all__'