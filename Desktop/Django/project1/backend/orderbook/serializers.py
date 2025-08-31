from django.forms import CharField, ValidationError
from rest_framework.serializers import Serializer, SlugRelatedField
from rest_framework import serializers
from decimal import Decimal, InvalidOperation
from .models import Instrument, Order, Trade

class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = ['id', 'symbol', 'name', 'instrument_type', 'is_active']
        
class OrderSerializer(serializers.ModelSerializer):
    instrument_symbol = serializers.CharField(source='instrument.symbol', read_only=True)
    instrument_name = serializers.CharField(source='instrument.name', read_only=True)
    
    fill_percentage = serializers.SerializerMethodField()
    order_value = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'instrument_symbol', 'instrument_name',
            'order_type', 'price', 'instrument', 'original_quantity', 
            'remaining_quantity', 'filled_quantity', 'status', 
            'fill_percentage', 'order_value', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order_id', 'filled_quantity', 'created_at', 'updated_at'
        ]
    
    def get_fill_percentage(self, obj):
        return round(obj.fill_percentage, 2)
    
    def get_order_value(self, obj):
        return float(obj.price * obj.original_quantity)
    
    def validate(self, data):
        if data.get('remaining_quantity', 0) > data.get('original_quantity', 0):
            raise serializers.ValidationError(
                "Remaining quantity cannot exceed original quantity"
            )
        
        if data.get('price') and data['price'] <= 0:
            raise serializers.ValidationError("Price must be positive")
            
        return data

class CreateOrderSerializer(serializers.ModelSerializer):
    instrument = serializers.SlugRelatedField(
        slug_field='symbol',
        queryset=Instrument.objects.filter(is_active=True)
    )
    
    class Meta:
        model = Order
        fields = [
            'instrument', 'order_type', 'price',
            'original_quantity'
        ]
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be positive")
        return value
    
    def create(self, data):
        data['remaining_quantity'] = data['original_quantity']
        return Order.object.create(**data)
    
class OrderBookItemSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=12, decimal_places=4)
    quantity = serializers.DecimalField(max_digits=20, decimal_places=4)
    order_count = serializers.IntegerField()
    order_type = serializers.CharField()
    
class OrderBookSerializer(serializers.Serializer):
    instrument = InstrumentSerializer(read_only=True)
    bids = OrderBookItemSerializer(many=True, read_only=True)
    asks = OrderBookItemSerializer(many=True, read_only=True)
    spread = serializers.SerializerMethodField()
    updated_at = serializers.DateTimeField(read_only=True)
    
    def get_spread(self, obj):
        bids = obj.get('bids', [])
        asks = obj.get('asks', [])
        
        if not bids or not asks:
            return None
            
        best_bid = max(bids, key=lambda x: x['price'])['price']
        best_ask = min(asks, key=lambda x: x['price'])['price']
        
        return {
            'absolute': float(best_ask - best_bid),
            'percentage': float(((best_ask - best_bid) / best_ask) * 100) if best_ask > 0 else 0,
            'best_bid': float(best_bid),
            'best_ask': float(best_ask)
        }
        
class TradeSerializer(serializers.ModelSerializer):
    instrument_symbol = serializers.CharField(source='instrument.symbol', read_only=True)
    trade_value = serializers.SerializerMethodField()
    
    class Meta:
        model = Trade
        fields = [
            'id', 'trade_id', 'instrument', 'instrument_symbol',
            'quantity', 'trade_value', 'created_at'
        ]
    
    def get_trade_value(self, obj):
        return float(obj.sell_order.price * obj.quantity)
        
class OrderHistorySerializer(serializers.ModelSerializer):
    instrument_symbol = serializers.CharField(source='instrument.symbol', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'instrument_symbol', 'order_type',
            'price', 'original_quantity', 'filled_quantity', 
            'status', 'created_at'
        ]
        
class OrderStatsSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    active_orders = serializers.IntegerField()
    filled_orders = serializers.IntegerField()
    partial_orders = serializers.IntegerField()
    cancelled_orders = serializers.IntegerField()
    total_volume = serializers.DecimalField(max_digits=20, decimal_places=2)
    avg_order_size = serializers.DecimalField(max_digits=12, decimal_places=2)
    instruments_count = serializers.IntegerField()

class InstrumentStatsSerializer(serializers.Serializer):
    instrument = InstrumentSerializer()
    order_count = serializers.IntegerField()
    total_volume = serializers.DecimalField(max_digits=20, decimal_places=2)
    avg_price = serializers.DecimalField(max_digits=12, decimal_places=4)
    last_trade_price = serializers.DecimalField(max_digits=12, decimal_places=4, allow_null=True)
    last_trade_time = serializers.DateTimeField(allow_null=True)