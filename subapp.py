"""
Tour de France Analytics System - Subapp Companion Launcher
BT5110 Data Management & Warehousing - Group 39
Team: Sharon, Keerthivasan, Louise, Sulistyo
"""

import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 70)
    print("🚴 Tour de France Interactive OLAP Dashboard (BT5110 - Group 39)")
    print("=" * 70)
    print("Contributors: James Sharon Susan, Keerthivasan Radhakrishnan, Louise, Sulistyo Agung Wibowo\n")
    print("To launch the interactive dashboard in your browser, run:")
    print("   streamlit run main.py")
    print("\nOr using your exact python environment:")
    print(f"   \"{sys.executable}\" -m streamlit run main.py\n")
    print("Starting Streamlit now...\n")
    
    app_path = Path(__file__).parent / "main.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])

if __name__ == "__main__":
    main()
