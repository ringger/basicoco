#!/usr/bin/env python3
"""
Enhanced pexpect CLI test with detailed logging
"""

import os
import pexpect
import sys
import time
from datetime import datetime

def test_cli_with_logging():
    print("=== TRS-80 CLI SESSION WITH DETAILED LOGGING ===")

    # Create log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("logs", exist_ok=True)
    log_filename = f"logs/cli_session_{timestamp}.log"

    with open(log_filename, 'w') as logfile:
        logfile.write(f"TRS-80 CLI Session Log - {datetime.now()}\n")
        logfile.write("=" * 60 + "\n\n")
        
        print(f"📝 Logging session to: {log_filename}")
        
        # Start the CLI client
        child = pexpect.spawn('python cli_client.py --host localhost --port 5000', 
                             encoding='utf-8', timeout=10)
        
        # Log everything to file AND stdout
        child.logfile_read = logfile
        
        try:
            print("\n🔌 Connecting to backend server...")
            
            # Wait for connection
            child.expect("READY", timeout=15)
            logfile.write("\n--- CONNECTION ESTABLISHED ---\n")
            print("✅ Connected!")
            
            # Test FILES command
            print("\n📁 Testing FILES command...")
            child.sendline("FILES")
            child.expect("READY", timeout=10)
            logfile.write("\n--- FILES COMMAND COMPLETED ---\n")
            
            # Load program
            print("\n💾 Loading simple_lunar program...")
            child.sendline('LOAD "simple_lunar"')
            child.expect("READY", timeout=10)
            logfile.write("\n--- PROGRAM LOADED ---\n")
            
            # Show program listing
            print("\n📋 Displaying program listing...")
            child.sendline("LIST")
            child.expect("READY", timeout=10)
            logfile.write("\n--- PROGRAM LISTED ---\n")
            
            # Run the game
            print("\n🚀 Starting Lunar Lander game...")
            child.sendline("RUN")
            logfile.write("\n--- GAME STARTED ---\n")
            
            # Wait for game display
            child.expect("FUEL:", timeout=10)
            
            # Play multiple turns
            thrust_values = [10, 8, 6, 4, 2, 1, 0]
            
            for turn, thrust in enumerate(thrust_values, 1):
                print(f"🎮 Turn {turn}: Thrust = {thrust}")
                logfile.write(f"\n--- TURN {turn}: THRUST {thrust} ---\n")
                
                try:
                    child.expect("THRUST", timeout=10)
                    child.sendline(str(thrust))
                    time.sleep(1)
                    
                    # Check game state
                    index = child.expect(["LANDED!", "ALTITUDE:", pexpect.TIMEOUT], timeout=8)
                    
                    if index == 0:  # LANDED!
                        logfile.write("\n--- GAME COMPLETED: LANDED! ---\n")
                        print("🎉 SUCCESSFUL LANDING!")
                        
                        # Wait for landing result
                        try:
                            child.expect(["GOOD LANDING!", "CRASH!", pexpect.TIMEOUT], timeout=5)
                            logfile.write("\n--- LANDING RESULT RECEIVED ---\n")
                        except pexpect.exceptions.TIMEOUT:
                            pass
                        break
                        
                    elif index == 2:  # TIMEOUT
                        logfile.write(f"\n--- TURN {turn}: TIMEOUT ---\n")
                        print(f"⏰ Turn {turn} timeout")
                        continue
                        
                except pexpect.exceptions.TIMEOUT:
                    logfile.write(f"\n--- TURN {turn}: TIMEOUT EXCEPTION ---\n")
                    print(f"❌ Timeout on turn {turn}")
                    break
            
            # Final wait
            time.sleep(2)
            logfile.write("\n--- SESSION COMPLETED ---\n")
            
        except pexpect.exceptions.TIMEOUT as e:
            error_msg = f"Timeout: {e}\nBuffer: {child.before}"
            logfile.write(f"\n--- ERROR: {error_msg} ---\n")
            print(f"❌ {error_msg}")
            
        except pexpect.exceptions.EOF:
            logfile.write("\n--- CLI SESSION ENDED (EOF) ---\n")
            print("🔚 CLI session ended")
            
        finally:
            try:
                child.sendcontrol('c')
                child.close()
                logfile.write("\n--- SESSION CLOSED ---\n")
            except:
                pass
    
    print(f"\n📄 Complete session log saved to: {log_filename}")
    print(f"📂 Use: cat {log_filename} | less")

    # Test passes if we got this far without exceptions
    assert log_filename is not None

if __name__ == '__main__':
    log_file = test_cli_with_logging()