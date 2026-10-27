import tkinter as tk
from tkinter import scrolledtext, font
import subprocess
import sys
import os
import threading
import time

class QuantAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Quantitative IV Surface Engine")
        self.root.geometry("680x560")
        self.root.configure(bg="#1e1e1e")

        # Custom Fonts
        title_font = font.Font(family="Arial", size=14, weight="bold")
        label_font = font.Font(family="Arial", size=10)
        btn_font = font.Font(family="Arial", size=10, weight="bold")

        # Header Title
        header_label = tk.Label(root, text="Volatility Surface & Skew Engine", font=title_font, fg="#ffffff", bg="#1e1e1e")
        header_label.pack(pady=15)

        # Input Frame
        input_frame = tk.Frame(root, bg="#1e1e1e")
        input_frame.pack(pady=5)

        tk.Label(input_frame, text="Enter Ticker Symbol:", font=label_font, fg="#cccccc", bg="#1e1e1e").pack(side=tk.LEFT, padx=5)
        
        self.ticker_entry = tk.Entry(input_frame, font=label_font, width=12, justify="center")
        self.ticker_entry.insert(0, "AAPL")
        self.ticker_entry.pack(side=tk.LEFT, padx=5)

        # Run Button
        self.run_btn = tk.Button(input_frame, text="Run Pipeline", font=btn_font, bg="#007acc", fg="#ffffff", activebackground="#005999", activeforeground="#ffffff", command=self.start_pipeline_thread, padx=10, pady=2)
        self.run_btn.pack(side=tk.LEFT, padx=10)

        # Output Terminal Box
        console_frame = tk.Frame(root, bg="#1e1e1e")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        tk.Label(console_frame, text="Octave Quantitative Results:", font=label_font, fg="#888888", bg="#1e1e1e", anchor="w").pack(fill=tk.X, pady=2)

        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, font=("Consolas", 10), bg="#121212", fg="#00ff66", insertbackground="white")
        self.console.pack(fill=tk.BOTH, expand=True)
        self.console.insert(tk.END, "[READY] System initialized. Enter a ticker and click 'Run Pipeline'.\n")

    def log(self, message):
        """Thread-safe logging to the UI console box."""
        self.console.insert(tk.END, message)
        self.console.see(tk.END)

    def start_pipeline_thread(self):
        """Runs the pipeline in a background thread so the GUI doesn't freeze."""
        ticker = self.ticker_entry.get().strip().upper()
        if not ticker:
            ticker = "AAPL"
            
        self.run_btn.config(state=tk.DISABLED, bg="#444444")
        self.console.delete(1.0, tk.END)
        
        # Start background thread
        threading.Thread(target=self.execute_pipeline, args=(ticker,), daemon=True).start()

    def execute_pipeline(self, ticker):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # --- STEP 0: Clean up old report to prevent stale data ---
            report_path = os.path.join(script_dir, "report.txt")
            if os.path.exists(report_path):
                try:
                    os.remove(report_path)
                except Exception:
                    pass

            # --- STEP 1: Run Python Data Fetcher ---
            self.log(f"[*] Fetching live market option chain for {ticker}...\n")
            
            fetch_process = subprocess.run(
                [sys.executable, "fetch_data.py", ticker],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=script_dir
            )
            
            if fetch_process.returncode != 0:
                self.log(f"\n[ERROR] Data fetching failed: {fetch_process.stderr}\n")
                self.enable_button()
                return

            self.log(f"[+] Market data successfully fetched and cleaned.\n")

            # --- STEP 2: Launch Full Octave GUI Engine ---
            self.log(f"[*] Executing numerical solver & rendering 3D surface...\n\n")
            
            octave_path = r"C:\Program Files\GNU Octave\Octave-11.1.0\mingw64\bin\octave.exe"
            if not os.path.exists(octave_path):
                octave_path = r"C:\Program Files\GNU Octave\Octave-11.1.0\bin\octave.exe"
                
            if not os.path.exists(octave_path):
                self.log(f"\n[ERROR] Could not find octave.exe at: {octave_path}\n")
                self.enable_button()
                return

            subprocess.Popen(
                [
                    octave_path, 
                    "--persist", 
                    "--eval", 
                    f"cd('{script_dir.replace(os.sep, '/') }'); iv_surface;"
                ],
                cwd=script_dir
            )

            # --- STEP 3: Wait For and Display Fresh Report ---
            for _ in range(50): # Wait up to 5 seconds for the new report to generate
                if os.path.exists(report_path):
                    break
                time.sleep(0.1)

            if os.path.exists(report_path):
                with open(report_path, "r") as f:
                    report_content = f.read()
                    self.log(report_content)
            else:
                self.log("\n[WARNING] Report file generation timed out.\n")

            self.log("\n[SUCCESS] 3D Native Octave windows launched successfully!\n")

        except Exception as e:
            self.log(f"\n[ERROR] System Exception: {e}\n")
            
        finally:
            self.enable_button()

    def enable_button(self):
        self.run_btn.config(state=tk.NORMAL, bg="#007acc")

if __name__ == "__main__":
    root = tk.Tk()
    app = QuantAppGUI(root)
    root.mainloop()