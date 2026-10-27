import sys
import os
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.io import savemat

# Grab ticker from command-line argument, default to AAPL
ticker_symbol = sys.argv[1].upper() if len(sys.argv) > 1 else "AAPL"
print(f"Fetching real-world option chain for {ticker_symbol}...")

stock = yf.Ticker(ticker_symbol)
hist = stock.history(period="5d")
spot_price = hist['Close'].iloc[-1]
risk_free_rate = 0.045

expirations = stock.options
selected_exp = expirations[:min(5, len(expirations))]

common_strikes = np.linspace(spot_price * 0.93, spot_price * 1.07, 22)
maturities_list = []
price_matrix = []
today = pd.Timestamp.today()

for exp in selected_exp:
    opt_chain = stock.option_chain(exp)
    calls = opt_chain.calls
    
    exp_date = pd.Timestamp(exp)
    T = (exp_date - today).days / 365.0
    if T <= 0:
        continue
        
    calls = calls[(calls['bid'] > 0) & (calls['ask'] > 0)]
    if len(calls) < 3:
        continue
        
    maturities_list.append(T)
    calls['mid'] = (calls['bid'] + calls['ask']) / 2
    valid_calls = calls.sort_values('strike')
    
    interp_prices = np.interp(
        common_strikes, 
        valid_calls['strike'].values, 
        valid_calls['mid'].values, 
        left=np.nan, 
        right=np.nan
    )
    price_matrix.append(interp_prices)

price_matrix = np.array(price_matrix)
df_prices = pd.DataFrame(price_matrix).interpolate(axis=1).bfill().ffill()
price_matrix = df_prices.values

K_grid, T_grid = np.meshgrid(common_strikes, maturities_list)

base_dir = os.path.dirname(os.path.abspath(__file__))
# Save to universal market_data.mat so Octave loads the correct ticker dynamically
file_path = os.path.join(base_dir, 'market_data.mat')

savemat(file_path, {
    'S': spot_price,
    'r': risk_free_rate,
    'K': K_grid,
    'T': T_grid,
    'market_prices': price_matrix,
    'ticker_name': ticker_symbol  # Passed dynamically to Octave
})

print(f"Success! {ticker_symbol} data saved successfully.")