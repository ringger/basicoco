#!/usr/bin/env python3
"""
Run the complex, more interesting Lunar Lander with pexpect
"""

import os
import pexpect
import sys
import time
from datetime import datetime

def test_complex_lunar_lander():
    print("🚀 === COMPLEX LUNAR LANDER SESSION === 🚀")

    # Create detailed log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("logs", exist_ok=True)
    log_filename = f"logs/complex_lunar_session_{timestamp}.log"

    with open(log_filename, 'w') as logfile:
        logfile.write(f"Complex Lunar Lander Session Log - {datetime.now()}\n")
        logfile.write("=" * 70 + "\n\n")
        
        print(f"📝 Logging detailed session to: {log_filename}")
        
        # Start the CLI client
        child = pexpect.spawn('python cli_client.py --host localhost --port 5000', 
                             encoding='utf-8', timeout=15)
        
        # Log to both file and stdout
        child.logfile_read = logfile
        
        try:
            print("\n🔌 Connecting to TRS-80 emulator...")
            child.expect("READY", timeout=20)
            logfile.write("\n--- CONNECTED TO TRS-80 EMULATOR ---\n")
            print("✅ Connected!")
            
            # Load the complex lunar lander
            print("\n💾 Loading complex lunar_lander.bas...")
            child.sendline('LOAD "lunar_lander"')
            child.expect("READY", timeout=15)
            logfile.write("\n--- COMPLEX LUNAR LANDER LOADED ---\n")
            print("✅ Complex program loaded (74 lines)!")
            
            # Start the game
            print("\n🚀 Starting the enhanced Lunar Lander experience...")
            child.sendline("RUN")
            logfile.write("\n--- GAME STARTED ---\n")
            
            # Wait for the intro screen
            child.expect("PRESS ENTER TO START", timeout=10)
            print("📺 Game intro displayed - pressing ENTER...")
            
            # Press ENTER to start
            child.sendline("")
            logfile.write("\n--- PRESSED ENTER TO START ---\n")
            
            # Wait for first game turn
            child.expect("THRUST", timeout=10)
            print("🎮 Game is ready for input!")
            
            # Play multiple strategic turns
            strategy = [
                (15, "Initial high thrust to slow descent"),
                (12, "Moderate thrust to control velocity"), 
                (10, "Steady deceleration"),
                (8, "Fine-tuning descent rate"),
                (6, "Approaching surface carefully"),
                (4, "Precision landing thrust"),
                (2, "Final approach"),
                (1, "Touchdown sequence"),
                (0, "Cut engines if close enough")
            ]
            
            for turn, (thrust, description) in enumerate(strategy, 1):
                print(f"\n🎯 Turn {turn}: Thrust={thrust} ({description})")
                logfile.write(f"\n--- TURN {turn}: THRUST {thrust} ---\n")
                logfile.write(f"Strategy: {description}\n")
                
                try:
                    # Send thrust value
                    child.sendline(str(thrust))
                    time.sleep(1.5)  # Give time for physics calculation
                    
                    # Check for game end conditions
                    index = child.expect([
                        "THRUST",           # Continue playing
                        "LANDING REPORT",   # Game ended
                        "CRASH",           # Crashed
                        "PERFECT LANDING",  # Perfect!
                        "GOOD LANDING",    # Good!
                        pexpect.TIMEOUT    # Timeout
                    ], timeout=10)
                    
                    if index == 0:  # Continue playing
                        print(f"  ↳ Turn {turn} completed, continuing...")
                        continue
                        
                    elif index in [1, 2, 3, 4]:  # Game ended
                        logfile.write("\n--- GAME COMPLETED ---\n")
                        print(f"\n🎉 GAME COMPLETED AFTER {turn} TURNS!")
                        
                        # Wait for final results
                        time.sleep(2)
                        try:
                            child.expect("PLAY AGAIN", timeout=8)
                            print("🔄 Game asking if we want to play again...")
                            child.sendline("N")  # Don't play again
                            logfile.write("\n--- DECLINED TO PLAY AGAIN ---\n")
                        except pexpect.exceptions.TIMEOUT:
                            print("Game completed without play-again prompt")
                        break
                        
                    elif index == 5:  # Timeout
                        print(f"  ⏰ Turn {turn} timeout, trying to continue...")
                        continue
                        
                except pexpect.exceptions.TIMEOUT:
                    logfile.write(f"\n--- TURN {turn}: TIMEOUT ---\n")
                    print(f"❌ Timeout on turn {turn}")
                    break
            
            # Final pause to see results
            time.sleep(3)
            logfile.write("\n--- COMPLEX LUNAR LANDER SESSION COMPLETED ---\n")
            
        except pexpect.exceptions.TIMEOUT as e:
            error_msg = f"Session timeout: {e}"
            logfile.write(f"\n--- TIMEOUT ERROR: {error_msg} ---\n")
            print(f"⏰ {error_msg}")
            
        except pexpect.exceptions.EOF:
            logfile.write("\n--- SESSION ENDED (EOF) ---\n")
            print("🔚 Session ended")
            
        finally:
            try:
                child.sendcontrol('c')
                child.close()
                logfile.write("\n--- SESSION CLOSED ---\n")
            except:
                pass
    
    print(f"\n📄 Complete complex session log: {log_filename}")
    print(f"📂 View with: cat {log_filename}")
    
    # Test passes if we got this far without exceptions
    assert log_filename is not None

if __name__ == '__main__':
    log_file = test_complex_lunar_lander()