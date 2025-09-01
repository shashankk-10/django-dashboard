from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

class Instrument(models.Model):
    INSTRUMENT_TYPES = [
        ('STOCK', 'Stock'),
        ('OPTION', 'Option'),
        ('FUTURE', 'Future'),
        ('FX', 'Foreign Exchange'),
    ]
    
    symbol = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    instrument_type = models.CharField(max_length=10, choices=INSTRUMENT_TYPES)
    exchange = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['symbol', 'exchange']),
            models.Index(fields=['instrument_type']),
        ]
    
    def __str__(self):
        return f"{self.symbol} ({self.exchange})"

class Position(models.Model):
    POSITION_SIDE = [('LONG', 'Long'), ('SHORT', 'Short')]
    
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    quantity = models.DecimalField(
        max_digits=15, 
        decimal_places=8,
        validators=[MinValueValidator(Decimal('0.00000001'))]
    )
    avg_cost = models.DecimalField(max_digits=12, decimal_places=4)
    current_price = models.DecimalField(max_digits=12, decimal_places=4)
    side = models.CharField(max_length=5, choices=POSITION_SIDE, default='LONG')
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['instrument', 'last_updated']),
            models.Index(fields=['last_updated']),
        ]
        unique_together = ['instrument']
    
    def clean(self):
        if self.quantity == 0:
            raise models.ValidationError("Quantity cannot be zero")
    
    @property
    def market_value(self):
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self):
        if self.side == 'LONG':
            return (self.current_price - self.avg_cost) * self.quantity
        else:
            return (self.avg_cost - self.current_price) * self.quantity
    
    @property
    def pnl_percentage(self):
        if self.avg_cost and self.avg_cost != 0:
            cost_basis = self.avg_cost * abs(self.quantity)
            return (self.unrealized_pnl / cost_basis) * 100
        return Decimal('0')
    
    def __str__(self):
        return f"{self.instrument.symbol}: {self.quantity} @ {self.current_price}"

class Trade(models.Model):
    SIDE_CHOICES = [('BUY', 'Buy'), ('SELL', 'Sell')]
    
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    quantity = models.DecimalField(
        max_digits=15, 
        decimal_places=8,
        validators=[MinValueValidator(Decimal('0.00000001'))]
    )
    price = models.DecimalField(max_digits=12, decimal_places=4)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['instrument', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['side', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.side} {self.quantity} {self.instrument.symbol} @ {self.price}"

class MarketData(models.Model):
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    bid_price = models.DecimalField(max_digits=12, decimal_places=4)
    ask_price = models.DecimalField(max_digits=12, decimal_places=4)
    last_price = models.DecimalField(max_digits=12, decimal_places=4)
    volume = models.BigIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['instrument', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    @property
    def spread(self):
        return self.ask_price - self.bid_price
    
    @property
    def spread_percentage(self):
        mid_price = (self.bid_price + self.ask_price) / 2
        return (self.spread / mid_price) * 100 if mid_price else 0
    
    def __str__(self):
        return f"{self.instrument.symbol}: {self.last_price} @ {self.timestamp}"