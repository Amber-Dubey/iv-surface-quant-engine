import subprocess
import sys
import os

def main():
    print("==================================================")
    print("   QUANTITATIVE IV SURFACE TERMINAL ORCHESTRATOR  ")
    print("==================================================")
    
    # Prompt user for stock ticker
    ticker = input("Enter stock ticker symbol (e.g., AAPL, NVDA, MSFT): ").strip().upper()
    if not ticker:
        ticker = "AAPL"
        
    print(f"\n[1/2] Fetching live market option chain for {ticker}...")
    # Use active virtual environment's python interpreter
    subprocess.run([sys.executable, "fetch_data.py", ticker], check=True)
    
    print(f"\n[2/2] Launching GNU Octave Native Engine...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Exact path pointing to your Octave 11.1.0 installation
    octave_path = r"C:\Program Files\GNU Octave\Octave-11.1.0\mingw64\bin\octave-cli.exe"
    
    # Fallback check if mingw64 path differs
    if not os.path.exists(octave_path):
        octave_path = r"C:\Program Files\GNU Octave\Octave-11.1.0\bin\octave-cli.exe"
        
    if not os.path.exists(octave_path):
        print(f"\n[ERROR] Could not find octave-cli.exe at: {octave_path}")
        sys.exit(1)
        
    print(f"[INFO] Using Octave binary at: {octave_path}")
    
    try:
        # Run Octave with --persist so windows stay open interactively
        subprocess.run([
            octave_path, 
            "--persist", 
            "--eval", 
            f"cd('{script_dir.replace(os.sep, '/') }'); iv_surface;"
        ], check=True)
    except Exception as e:
        print(f"\n[ERROR] Failed to execute Octave process: {e}")
        sys.exit(1)
        
    print("\n[INFO] Octave session closed. Pipeline execution complete!")

if __name__ == "__main__":
    main()