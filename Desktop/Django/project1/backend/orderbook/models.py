import uuid
from django.db import models
from django.core.exceptions import ValidationError


# Create your models here.
class Instrument(models.Model):
    INSTRUMENT_TYPE = [
        ('STOCK', 'Stock'),
        ('OPTION', 'Option'),
        ('FUTURE', 'Future')
    ]
    
    instrument_type = models.CharField(choices=INSTRUMENT_TYPE)
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=20)
    is_active=models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table='instruments'
        ordering = ['symbol']

class Order(models.Model):
    ORDER_TYPE =[
        ('SELL', 'Sell'),
        ('BUY', 'Buy')
    ]
    
    ORDER_STATUS = [
        ('ACTIVE', 'Active'),
        ('FILLED', 'Filled'),
        ('CANCELLED', 'Cancelled'),
        ('PARTIAL', 'Partially Filled'),
    ]
    
    order_id=models.UUIDField(default=uuid.uuid4, unique=True)
    order_type = models.CharField(choices=ORDER_TYPE)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    original_quantity = models.PositiveIntegerField()
    remaining_quantity = models.PositiveIntegerField()
    filled_quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(choices=ORDER_STATUS, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        
        indexes = [
            models.Index(
                fields = ['instrument', 'order_type', 'price'],
                name='idx_order_type_price',
                condition=models.Q(status='ACTIVE', remaining_quantity__gt=0)
            ),
            models.Index(
                fields=['instrument', 'status'],
                name='idx_instrument_order_status',
                condition=models.Q(status='ACTIVE')
            ),
            models.Index(
                fields=['instrument', '-created_at'],
                name='idx_orders_instrument_time'
            )
        ]
        
    def clean(self):
        # Ensure quantities add up
        if self.filled_quantity + self.remaining_quantity != self.original_quantity:
            raise ValidationError("Filled + Remaining must equal Original Quantity")
        
        # Price validation
        if self.price <= 0:
            raise ValidationError("Price must be positive")

    def save(self, *args, **kwargs):
        self.filled_quantity = self.original_quantity - self.remaining_quantity

        if self.remaining_quantity == 0:
            self.status = 'FILLED'
        elif self.filled_quantity > 0:
            self.status = 'PARTIAL'
        
        super().save(*args, **kwargs)
    
    @property
    def fill_percentage(self):
        if self.original_quantity == 0:
            return 0
        return (self.filled_quantity/self.original_quantity) * 100

class Trade(models.Model):
    trade_id = models.UUIDField(uuid.uuid4, unique=True)
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name='trades')
    buy_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='buy_trade')
    sell_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='sell_trade')
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'trades'
        ordering = ['-created_at']
        
        indexes = [
            models.Index(
                fields = ['-created_at']
            ),
            models.Index(
                fields = ['instrument', '-created_at']
            )
        ]
    

