import os
import subprocess
import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="IV Surface Quant Engine", layout="centered")

st.title("Quantitative Implied Volatility Surface Engine")
st.write("Hybrid Control Panel: Python/Streamlit Frontend + Native GNU Octave Visualizer")

# Sidebar Configuration
st.sidebar.header("Market & System Settings")
ticker_symbol = st.sidebar.text_input("Stock Ticker", value="AAPL")

# NOTE: Using octave.exe instead of octave-cli.exe ensures native figure windows pop up
octave_path_input = st.sidebar.text_input(
    "Path to octave.exe", 
    value=r"C:\Program Files\GNU Octave\Octave-11.1.0\mingw64\bin\octave.exe"
)

if st.button("Launch Octave Simulation Engine"):
    with st.spinner(f"Fetching real-world option chain for {ticker_symbol.upper()} and launching Octave engine..."):
        try:
            # 1. Fetch live market data via yfinance
            stock = yf.Ticker(ticker_symbol.strip().upper())
            hist = stock.history(period="5d")
            
            if hist.empty:
                raise ValueError(f"Could not fetch market data for ticker: {ticker_symbol}. Check symbol.")
                
            spot_price = hist['Close'].iloc[-1]
            expirations = stock.options
            
            if not expirations:
                raise ValueError(f"No option expiration chains found for {ticker_symbol}.")
                
            selected_exp = expirations[:min(6, len(expirations))]
            
            common_strikes = np.linspace(spot_price * 0.85, spot_price * 1.15, 20)
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
                    
                maturities_list.append(T)
                
                calls['mid'] = (calls['bid'] + calls['ask']) / 2
                calls['mid'] = calls['mid'].fillna(calls['lastPrice'])
                
                valid_calls = calls.dropna(subset=['mid']).sort_values('strike')
                
                if len(valid_calls) > 2:
                    interp_prices = np.interp(
                        common_strikes, 
                        valid_calls['strike'].values, 
                        valid_calls['mid'].values, 
                        left=np.nan, 
                        right=np.nan
                    )
                    price_matrix.append(interp_prices)
                else:
                    price_matrix.append(np.ones_like(common_strikes) * np.nan)
                    
            price_matrix = np.array(price_matrix)
            
            # Clean up NaNs using Black-Scholes intrinsic value floor fallback
            for r_idx in range(price_matrix.shape[0]):
                for c_idx in range(price_matrix.shape[1]):
                    if np.isnan(price_matrix[r_idx, c_idx]):
                        strike_val = common_strikes[c_idx]
                        price_matrix[r_idx, c_idx] = max(0.0, spot_price - strike_val) + 0.5
            
            K_grid, T_grid = np.meshgrid(common_strikes, maturities_list)
            
            if price_matrix.shape[0] < 2:
                raise ValueError("Insufficient expiration data points to build a 2D surface.")

            # 2. Write parameters to params.m for Octave
            with open("params.m", "w") as f:
                f.write(f"S = {spot_price};\n")
                f.write(f"r = 0.045;\n")
                f.write("K = " + np.array_str(K_grid, precision=4, suppress_small=True).replace('\n', '') + ";\n")
                f.write("T = " + np.array_str(T_grid, precision=4, suppress_small=True).replace('\n', '') + ";\n")
                f.write("market_prices = " + np.array_str(price_matrix, precision=4, suppress_small=True).replace('\n', '') + ";\n")
            
            octave_path = octave_path_input.strip()
            if not os.path.exists(octave_path):
                raise FileNotFoundError(f"Could not find octave.exe at: {octave_path}. Update path in sidebar.")

            # 3. Trigger Octave to run the script and pop up native figures
            subprocess.run([octave_path, "--persist", "iv_surface.m"], check=True)
            
            st.success(f"Successfully fetched {ticker_symbol.upper()} data (${spot_price:.2f}) and spawned Octave graphic windows!")
            
        except Exception as e:
            st.error(f"Error during execution: {e}")
            
        # Cleanup temporary parameter file
        if os.path.exists("params.m"):
            os.remove("params.m")   