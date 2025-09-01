from django.contrib import admin
from .models import Instrument, Position, Trade, MarketData

@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'instrument_type', 'exchange']
    list_filter = ['instrument_type', 'exchange']
    search_fields = ['symbol', 'name']

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['instrument', 'quantity', 'avg_cost', 'current_price', 'side', 'last_updated']
    list_filter = ['side', 'last_updated']
    search_fields = ['instrument__symbol']

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['instrument', 'side', 'quantity', 'price', 'timestamp']
    list_filter = ['side', 'timestamp']
    search_fields = ['instrument__symbol']

@admin.register(MarketData)
class MarketDataAdmin(admin.ModelAdmin):
    list_display = ['instrument', 'last_price', 'bid_price', 'ask_price', 'volume', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['instrument__symbol']