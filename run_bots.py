import subprocess
import sys
import time
import os

def run_bots():
    try:
        print("🤖 Starting AegisIX Multi-Bot System...")
        
        # Start JavaScript bot
        js_bot = subprocess.Popen(
            ["node", "index.js"],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        print("✅ JavaScript bot started")
        
        # Small delay between starts
        time.sleep(2)
        
        # Start Python bot
        py_bot = subprocess.Popen(
            [sys.executable, "karma_bot.py"],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        print("✅ Python bot started")
        
        print("\n🎮 Both bots are now running!")
        print("Press Ctrl+C to stop both bots")
        
        # Wait for both processes
        js_bot.wait()
        py_bot.wait()
        
    except KeyboardInterrupt:
        print("\n⏳ Stopping bots...")
        js_bot.terminate()
        py_bot.terminate()
        
        # Wait for processes to end
        js_bot.wait()
        py_bot.wait()
        print("👋 All bots stopped")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'js_bot' in locals(): js_bot.terminate()
        if 'py_bot' in locals(): py_bot.terminate()

if __name__ == "__main__":
    run_bots()