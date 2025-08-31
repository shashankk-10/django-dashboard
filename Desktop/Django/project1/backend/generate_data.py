# scripts/generate_data.py
"""
High-performance data generation script for HFT order book simulation
Generates realistic trading data with proper price distributions and order patterns
"""

import os, sys, django, random, uuid
from collections import defaultdict
from decimal import Decimal
from django.db import transaction

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from orderbook.models import Instrument, Order, Trade

def generate_instruments():
    symbols = {
        "AAPL" : "Apple Inc.", 
        "GOOGL" : "Alphabet Inc.", 
        "MSFT" : "Microsoft Inc.", 
        "TSLA" : "Tesla Inc.", 
        "AMZN" : "Amazon Inc"
    }

    instrument_types = ["STOCK", "OPTION", "FUTURE"]
    
    instruments = []
    for sym, name in symbols.items():
        inst, _ = Instrument.objects.get_or_create(
            symbol=sym,
            defaults={
                "name": name, 
                "instrument_type": random.choice(instrument_types), 
                "is_active": True
            }
        )
        instruments.append(inst)
    return instruments

def random_price(base=100, vol=0.02):
    return Decimal(str(base * (1 + random.uniform(-vol, vol)))).quantize(Decimal("0.0001"))

def random_quantity():
    return random.choice([random.randint(1, 100), random.randint(100, 1000)])

def generate_orders(instruments, n):
    orders = []
    for _ in range(n):
        instrument = random.choice(instruments)
        quantity = random_quantity()
        remaining = random.randint(0, quantity)
        filled = quantity - remaining
        order = Order(
            order_id=uuid.uuid4(),
            instrument=instrument,
            order_type=random.choice(["BUY", "SELL"]),
            price=random_price(random.uniform(50,300)),
            original_quantity=quantity,
            remaining_quantity=remaining,
            filled_quantity=filled
        )
        order.status=compute_status_for_order(order)
        orders.append(order)


    Order.objects.bulk_create(orders, batch_size=500)
    return orders

def compute_status_for_order(order):
    if order.remaining_quantity == 0:
        return "FILLED"
    elif order.original_quantity - order.remaining_quantity > 0:
        return "PARTIAL"
    else:
        return "ACTIVE"

def generate_trades(n):
    """
    Match buy and sell orders to generate trades.
    Ensures consistent updates of quantities and statuses.
    """

    trades = []

    # Get active BUYs (highest price first) and SELLs (lowest price first)
    buys = list(Order.objects.filter(status="ACTIVE", order_type="BUY").order_by("-price", "created_at"))
    sells = list(Order.objects.filter(status="ACTIVE", order_type="SELL").order_by("price", "created_at"))

    i, j = 0, 0

    while i < len(buys) and j < len(sells):
        if n <= 0:
            break

        buy = buys[i]
        sell = sells[j]

        # Match only if BUY price >= SELL price
        if buy.price >= sell.price:
            qty = min(buy.remaining_quantity, sell.remaining_quantity)

            with transaction.atomic():
                # Create trade
                trade = Trade.objects.create(
                    trade_id=uuid.uuid4(),
                    instrument=buy.instrument,
                    buy_order=buy,
                    sell_order=sell,
                    quantity=qty
                )

                # Update BUY order
                buy.filled_quantity += qty
                buy.remaining_quantity -= qty
                buy.status = "FILLED" if buy.remaining_quantity == 0 else "PARTIAL"
                buy.save()

                # Update SELL order
                sell.filled_quantity += qty
                sell.remaining_quantity -= qty
                sell.status = "FILLED" if sell.remaining_quantity == 0 else "PARTIAL"
                sell.save()

                trades.append(trade)

                n -= 1

            # Move to next order if FILLED
            if buy.remaining_quantity == 0:
                i += 1
            if sell.remaining_quantity == 0:
                j += 1
        else:
            # No match possible → break out
            break

    return trades

def main():
    total_orders = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    total_trades = int(sys.argv[2]) if len(sys.argv) > 2 else 2000

    instruments = generate_instruments()
    orders = generate_orders(instruments, total_orders)
    trades = generate_trades(total_trades)

    print(f"\nTotal orders {len(orders)}")
    print(f"\nTotal trades {len(trades)}")

    print("\nData generation completed successfully!")

if __name__ == "__main__":
    main()