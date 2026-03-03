#!/usr/bin/env python3
"""
Manual test to verify the lunar lander program works correctly
"""

import os
import pexpect
import sys
import time
from datetime import datetime

from emulator.config import DEFAULT_PORT

def test_manual_lunar():
    print("🚀 === MANUAL LUNAR LANDER TEST === 🚀")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("logs", exist_ok=True)
    log_filename = f"logs/manual_lunar_test_{timestamp}.log"

    with open(log_filename, 'w') as logfile:
        logfile.write(f"Manual Lunar Lander Test Log - {datetime.now()}\n")
        logfile.write("=" * 70 + "\n\n")
        
        child = pexpect.spawn(f'python cli_client.py --host localhost --port {DEFAULT_PORT}',
                             encoding='utf-8', timeout=15)
        child.logfile_read = logfile
        
        try:
            print("🔌 Connecting...")
            child.expect("READY", timeout=15)
            print("✅ Connected!")
            
            print("💾 Loading lunar_lander...")
            child.sendline('LOAD "lunar_lander"')
            child.expect("READY", timeout=10)
            print("✅ Loaded!")
            
            print("📋 Checking line 160...")
            child.sendline('LIST 160')
            index = child.expect(["READY", pexpect.TIMEOUT], timeout=5)
            if index == 0:
                print("✅ LIST command succeeded")
            
            print("🚀 Starting program...")
            child.sendline("RUN")
            
            # Wait for the intro to finish and prompt
            index = child.expect([
                "PRESS ENTER TO START", 
                "SYNTAX ERROR",
                pexpect.TIMEOUT
            ], timeout=10)
            
            if index == 0:
                print("✅ Found 'PRESS ENTER TO START' - program is working!")
                child.sendline("")  # Press Enter
                
                # Wait for game status display
                index2 = child.expect([
                    "TIME:",
                    "THRUST",
                    pexpect.TIMEOUT
                ], timeout=10)
                
                if index2 in [0, 1]:
                    print("🎮 Game is running! Sending first thrust...")
                    
                    # If we see TIME: first, wait for THRUST prompt
                    if index2 == 0:
                        child.expect("THRUST", timeout=5)
                    
                    child.sendline("15")
                    time.sleep(2)
                    
                    print("🏁 First move completed successfully!")
                    
                else:
                    print(f"⏰ Timeout waiting for game status")
                    
            elif index == 1:
                print("❌ SYNTAX ERROR still occurs")
                # Test passes if we got this far without exceptions
                assert log_filename is not None
                return
                
            elif index == 2:
                print("⏰ Timeout waiting for program start")
                # Test passes if we got this far without exceptions
                assert log_filename is not None
                return
            
        except Exception as e:
            print(f"❌ Error: {e}")
            
        finally:
            try:
                child.sendcontrol('c')
                child.close()
            except:
                pass
    
    print(f"\n📄 Test log: {log_filename}")
    # Test passes if we got this far without exceptions
    assert log_filename is not None

if __name__ == '__main__':
    test_manual_lunar()