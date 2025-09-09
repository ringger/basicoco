#!/usr/bin/env python3
"""
Debug lunar lander step by step
"""

import pexpect
import sys
import time
from datetime import datetime

def debug_lunar():
    print("🔍 === DEBUG LUNAR LANDER === 🔍")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/debug_lunar_{timestamp}.log"
    
    with open(log_filename, 'w') as logfile:
        child = pexpect.spawn('python cli_client.py --host localhost --port 5000', 
                             encoding='utf-8', timeout=30)
        child.logfile_read = logfile
        
        try:
            print("🔌 Connecting...")
            child.expect("READY", timeout=15)
            print("✅ Connected!")
            
            print("💾 Loading...")
            child.sendline('LOAD "lunar_lander"')
            child.expect("READY", timeout=10)
            print("✅ Loaded!")
            
            print("📋 Listing first few lines...")
            child.sendline('LIST 10-170')
            child.expect("READY", timeout=10)
            print("✅ Listed!")
            
            print("🚀 Starting RUN...")
            child.sendline("RUN")
            
            print("⏰ Waiting 10 seconds to see what happens...")
            time.sleep(10)
            
            print("🛑 Sending Ctrl+C to stop...")
            child.sendcontrol('c')
            
        except Exception as e:
            print(f"❌ Error: {e}")
            
        finally:
            try:
                child.close()
            except:
                pass
    
    print(f"\n📄 Debug log: {log_filename}")
    return log_filename

if __name__ == '__main__':
    debug_lunar()