from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy 
from lumibot.traders import Trader # Lumibot voornamelijk makkelijk algoritme framework
from datetime import datetime # Dit is om een tijdsinschatting binnen python te maken
from alpaca_trade_api import REST # Verzameld nieuwsberichten
from timedelta import Timedelta  # Rekend het verschil in tijd uit
from finbert_utils import estimate_sentiment

API_KEY = "PKPVNQ861E7IYCK3Q1EK" 
API_SECRET = "hbnHCfZ3HvanmHVsb3Yk7yyCr2S1UA00DZkGzJAs" 
BASE_URL = "https://paper-api.alpaca.markets/v2"

ALPACA_CREDS = {
    "API_KEY":API_KEY, 
    "API_SECRET": API_SECRET, 
    "PAPER": True
}

class MLTrader(Strategy): 
    def initialize(self, symbol:str="SPY", cash_at_risk:float=.5): # een hoger nummer hier zorgt dat hij meer geld uit geeft per trade. # Dit is de basis info die hij nodigt heeft om te runnen. Zie het als de brandstof in een auto.
        self.symbol = symbol
        self.sleeptime = "24H" 
        self.last_trade = None 
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET) #hier wordt het nieuws vandaan getoverd

    def position_sizing(self): #dit stukje code zorgt ervoor dat je niet zomaar een x aantal van iets koopt
        cash = self.get_cash() 
        last_price = self.get_last_price(self.symbol)
        quantity = round(cash * self.cash_at_risk / last_price,0) #hoeveel trades kunnen we kopen op basis van het geld dat beschikbaar is
        return cash, last_price, quantity 

    def get_dates(self): 
        today = self.get_datetime()
        three_days_prior = today - Timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d') # Hier zorgt hij dat dat hij nieuws van 3 dagen geleden omzet in eventuele trades.

    def get_sentiment(self): 
        today, three_days_prior = self.get_dates() #nieuws verzamelen
        news = self.api.get_news(symbol=self.symbol, 
                                 start=three_days_prior, 
                                 end=today) 
        news = [ev.__dict__["_raw"]["headline"] for ev in news] #nieuws formateren
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment  # resultaat nieuws

    def on_trading_iteration(self):   # dit geeft aan op basis van welke iteratie hij bezig blijft. # de kaders voor het uitvoerende gedeelte 
        cash, last_price, quantity = self.position_sizing() 
        probability, sentiment = self.get_sentiment()

        if cash > last_price: 
            if sentiment == "positive" and probability > .999: # Hier wordt het resultaat van het nieuws opgehaald om een trade te plaaten (buy order)
                if self.last_trade == "sell": 
                    self.sell_all() 
                order = self.create_order(
                    self.symbol, 
                    quantity, 
                    "buy", 
                    type="bracket", 
                    take_profit_price=last_price*1.20, 
                    stop_loss_price=last_price*.95
                )
                self.submit_order(order) 
                self.last_trade = "buy"
            elif sentiment == "negative" and probability > .999:  # Dit zorgt ervoor dat als er een negatief bericht naar buiten komt de trade wordt verkocht (sell order)
                if self.last_trade == "buy": 
                    self.sell_all() 
                order = self.create_order(
                    self.symbol, 
                    quantity, 
                    "sell", 
                    type="bracket", # zowel een limietorder als een stop-loss-order plaatst voor een aandeel dat hij/zij wilt kopen of verkopen
                    take_profit_price=last_price*.8, 
                    stop_loss_price=last_price*1.05
                )
                self.submit_order(order) 
                self.last_trade = "sell"

start_date = datetime(2022,6,23)
end_date = datetime(2024,6,23) 
broker = Alpaca(ALPACA_CREDS) 
strategy = MLTrader(name='mlstrat', broker=broker, 
                    parameters={"symbol":"SPY", 
                                "cash_at_risk":.5})
strategy.backtest(
    YahooDataBacktesting, 
  start_date, 
  end_date, 
  parameters={"symbol":"SPY", "cash_at_risk":.5}
)

# trader = Trader()
# trader.add_strategy(strategy)
# trader.run_all()
