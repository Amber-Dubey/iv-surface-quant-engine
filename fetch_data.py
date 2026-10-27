import os
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.io import savemat

print("Fetching and cleaning real-world option chain for AAPL...")
stock = yf.Ticker("AAPL")
hist = stock.history(period="5d")
spot_price = hist['Close'].iloc[-1]
risk_free_rate = 0.045 # 4.5%

expirations = stock.options
# Select near-term liquid expirations
selected_exp = expirations[:min(5, len(expirations))]

# TIGHTENED STRIKE RANGE: Focus on liquid ATM options (93% to 107% of spot)
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
        
    # Filter strictly for options with active bids and asks to avoid dead ticks
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

# Drop any expiration rows that ended up with too many NaNs
valid_rows = ~np.isnan(price_matrix).all(axis=1)
price_matrix = price_matrix[valid_rows]
maturities_list = np.array(maturities_list)[valid_rows]

# Fill remaining interior gaps smoothly using linear interpolation along columns
df_prices = pd.DataFrame(price_matrix).interpolate(axis=1).bfill().ffill()
price_matrix = df_prices.values

K_grid, T_grid = np.meshgrid(common_strikes, maturities_list)

base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, 'aapl_real_data.mat')

savemat(file_path, {
    'S': spot_price,
    'r': risk_free_rate,
    'K': K_grid,
    'T': T_grid,
    'market_prices': price_matrix
})

print(f"Success! Cleaned & Trimmed AAPL data saved (Spot: ${spot_price:.2f})")