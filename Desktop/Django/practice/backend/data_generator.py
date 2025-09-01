import os
import django
import random
import time
from decimal import Decimal
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from portfolio.models import Instrument, Position, Trade, MarketData

def generate_sample_data():
    print("🚀 Generating sample trading data...")
    
    # Create instruments
    instruments_data = [
        ('AAPL', 'Apple Inc.', 'STOCK', 'NASDAQ'),
        ('GOOGL', 'Alphabet Inc.', 'STOCK', 'NASDAQ'),
        ('MSFT', 'Microsoft Corp.', 'STOCK', 'NASDAQ'),
        ('TSLA', 'Tesla Inc.', 'STOCK', 'NASDAQ'),
        ('AMZN', 'Amazon.com Inc.', 'STOCK', 'NASDAQ'),
        ('META', 'Meta Platforms Inc.', 'STOCK', 'NASDAQ'),
        ('NVDA', 'NVIDIA Corp.', 'STOCK', 'NASDAQ'),
        ('EURUSD', 'EUR/USD', 'FX', 'FX'),
        ('GBPUSD', 'GBP/USD', 'FX', 'FX'),
        ('USDJPY', 'USD/JPY', 'FX', 'FX'),
    ]
    
    print("📊 Creating instruments...")
    instruments = []
    for symbol, name, inst_type, exchange in instruments_data:
        instrument, created = Instrument.objects.get_or_create(
            symbol=symbol,
            defaults={'name': name, 'instrument_type': inst_type, 'exchange': exchange}
        )
        instruments.append(instrument)
        if created:
            print(f"  ✅ Created {symbol}")
    
    # Generate positions
    print("💼 Generating positions...")
    positions_to_create = []
    for instrument in instruments:
        if instrument.instrument_type == 'STOCK':
            quantity = random.randint(100, 2000)
            base_price = random.uniform(50, 400)
        else:  # FX
            quantity = random.randint(10000, 100000)
            base_price = random.uniform(0.8, 1.5)
        
        # Create realistic avg_cost and current_price with some variance
        avg_cost = Decimal(str(round(base_price * random.uniform(0.95, 1.05), 4)))
        current_price = Decimal(str(round(base_price * random.uniform(0.92, 1.08), 4)))
        
        position = Position(
            instrument=instrument,
            quantity=Decimal(str(quantity)),
            avg_cost=avg_cost,
            current_price=current_price,
            side=random.choice(['LONG', 'SHORT'])
        )
        positions_to_create.append(position)
    
    # Bulk create positions
    Position.objects.all().delete()  # Clear existing
    Position.objects.bulk_create(positions_to_create)
    print(f"  ✅ Created {len(positions_to_create)} positions")
    
    # Generate trade history
    print("📈 Generating trade history...")
    Trade.objects.all().delete()  # Clear existing
    
    trades_batch = []
    total_trades = 300
    
    for i in range(total_trades):
        instrument = random.choice(instruments)
        
        if instrument.instrument_type == 'STOCK':
            quantity = random.randint(10, 500)
            price = random.uniform(50, 400)
        else:  # FX
            quantity = random.randint(1000, 50000)
            price = random.uniform(0.8, 1.5)
        
        trade = Trade(
            instrument=instrument,
            side=random.choice(['BUY', 'SELL']),
            quantity=Decimal(str(quantity)),
            price=Decimal(str(round(price, 4))),
            timestamp=datetime.now() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
        )
        trades_batch.append(trade)
        
        # Bulk create in batches
        if len(trades_batch) >= 50:
            Trade.objects.bulk_create(trades_batch)
            trades_batch = []
            time.sleep(0.05)  # Prevent CPU overload
            print(f"  📊 Generated {i+1}/{total_trades} trades...")
    
    # Create remaining trades
    if trades_batch:
        Trade.objects.bulk_create(trades_batch)
    
    # Generate market data
    print("💹 Generating market data...")
    MarketData.objects.all().delete()  # Clear existing
    
    market_data = []
    for instrument in instruments:
        if instrument.instrument_type == 'STOCK':
            last_price = random.uniform(50, 400)
        else:  # FX
            last_price = random.uniform(0.8, 1.5)
        
        # Create realistic bid/ask spread
        spread = last_price * random.uniform(0.001, 0.005)  # 0.1% to 0.5% spread
        bid_price = last_price - (spread / 2)
        ask_price = last_price + (spread / 2)
        
        market_data.append(MarketData(
            instrument=instrument,
            bid_price=Decimal(str(round(bid_price, 4))),
            ask_price=Decimal(str(round(ask_price, 4))),
            last_price=Decimal(str(round(last_price, 4))),
            volume=random.randint(10000, 1000000)
        ))
    
    MarketData.objects.bulk_create(market_data)
    print(f"  ✅ Created market data for {len(market_data)} instruments")
    
    # Summary
    print("\n🎉 Sample data generation completed!")
    print(f"📊 Summary:")
    print(f"   Instruments: {Instrument.objects.count()}")
    print(f"   Positions: {Position.objects.count()}")
    print(f"   Trades: {Trade.objects.count()}")
    print(f"   Market Data: {MarketData.objects.count()}")
    
    # Show portfolio summary
    total_positions = Position.objects.count()
    total_market_value = sum(float(p.market_value) for p in Position.objects.all())
    total_pnl = sum(float(p.unrealized_pnl) for p in Position.objects.all())
    
    print(f"\n💼 Portfolio Summary:")
    print(f"   Total Positions: {total_positions}")
    print(f"   Total Market Value: ${total_market_value:,.2f}")
    print(f"   Total P&L: ${total_pnl:,.2f}")
    print(f"   P&L %: {(total_pnl/total_market_value*100):+.2f}%")
    
    print(f"\n🌐 Ready to start server!")
    print(f"   Backend: python manage.py runserver")
    print(f"   Frontend: cd ../frontend && npm start")

if __name__ == '__main__':
    generate_sample_data()