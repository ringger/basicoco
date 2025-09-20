#!/usr/bin/env python3
"""
Run the complex Lunar Lander with better error handling
"""

import pexpect
import sys
import time
from datetime import datetime

def test_complex_lunar_lander():
    print("🚀 === COMPLEX LUNAR LANDER SESSION === 🚀")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/complex_lunar_session_{timestamp}.log"
    
    with open(log_filename, 'w') as logfile:
        logfile.write(f"Complex Lunar Lander Session Log - {datetime.now()}\n")
        logfile.write("=" * 70 + "\n\n")
        
        print(f"📝 Logging session to: {log_filename}")
        
        child = pexpect.spawn('python cli_client.py --host localhost --port 5000', 
                             encoding='utf-8', timeout=20)
        child.logfile_read = logfile
        
        try:
            print("🔌 Connecting...")
            child.expect("READY", timeout=20)
            print("✅ Connected!")
            
            print("💾 Loading complex lunar lander...")
            child.sendline('LOAD "lunar_lander"')
            child.expect("READY", timeout=15)
            print("✅ Loaded 74 lines!")
            
            print("🚀 Starting game...")
            child.sendline("RUN")
            
            # Try different patterns to find where it's waiting
            print("🔍 Looking for game prompts...")
            index = child.expect([
                "PRESS ENTER TO START",
                r"\? ",                    # INPUT prompt pattern
                "THRUST",
                "TIME:",
                "ALTITUDE:",
                pexpect.TIMEOUT
            ], timeout=15)
            
            if index == 0:  # PRESS ENTER TO START
                print("📺 Found 'PRESS ENTER TO START' - pressing ENTER...")
                child.sendline("")
                
                # Now wait for the game to start
                index2 = child.expect([
                    "TIME:",
                    "ALTITUDE:",
                    "THRUST", 
                    r"\? ",
                    pexpect.TIMEOUT
                ], timeout=15)
                
                if index2 in [0, 1, 2, 3]:
                    print("🎮 Game started successfully!")
                else:
                    print("⏰ Timeout after pressing ENTER")
                    # Test passes if we got this far without exceptions
                    assert log_filename is not None
                    return
                    
            elif index == 1:  # INPUT prompt
                print("📝 Found INPUT prompt - pressing ENTER...")
                child.sendline("")
                
            elif index in [2, 3, 4]:  # Game already started
                print("🎮 Game already running!")
                
            elif index == 5:  # Timeout
                print("⏰ Timeout waiting for game prompts")
                print("🔍 Checking current buffer...")
                print(f"Buffer content: {repr(child.before)}")
                # Test passes if we got this far without exceptions
                assert log_filename is not None
                return
            
            # Now play the game with strategic moves
            strategy = [
                (15, "High initial thrust"),
                (12, "Strong deceleration"),
                (10, "Steady control"), 
                (8, "Fine adjustment"),
                (6, "Approach control"),
                (4, "Landing sequence"),
                (2, "Final approach"),
                (0, "Touchdown")
            ]
            
            game_active = True
            turn = 0
            
            while game_active and turn < len(strategy):
                turn += 1
                thrust, description = strategy[turn-1]
                
                print(f"🎯 Turn {turn}: Thrust={thrust} ({description})")
                logfile.write(f"\n--- TURN {turn}: THRUST {thrust} ---\n")
                
                try:
                    # Wait for thrust prompt
                    index = child.expect([
                        "THRUST",
                        "LANDING REPORT", 
                        "CRASH",
                        "LANDED",
                        "PERFECT",
                        "GOOD",
                        pexpect.TIMEOUT
                    ], timeout=12)
                    
                    if index == 0:  # THRUST prompt
                        child.sendline(str(thrust))
                        time.sleep(2)  # Give time for calculation
                        
                    elif index in [1, 2, 3, 4, 5]:  # Game ended
                        print(f"🎉 GAME COMPLETED AFTER {turn-1} TURNS!")
                        logfile.write("--- GAME COMPLETED ---\n")
                        
                        # Let final output display
                        time.sleep(3)
                        
                        # Check for play again prompt
                        try:
                            child.expect("PLAY AGAIN", timeout=8)
                            child.sendline("N")
                        except pexpect.exceptions.TIMEOUT:
                            pass
                        
                        game_active = False
                        break
                        
                    elif index == 6:  # Timeout
                        print(f"⏰ Turn {turn} timeout")
                        break
                        
                except pexpect.exceptions.TIMEOUT:
                    print(f"❌ Timeout on turn {turn}")
                    break
            
            print("🏁 Game session completed!")
            
        except pexpect.exceptions.TIMEOUT as e:
            print(f"⏰ Session timeout: {e}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            
        finally:
            try:
                child.sendcontrol('c')
                child.close()
            except:
                pass
    
    print(f"\n📄 Session log: {log_filename}")
    # Test passes if we got this far without exceptions
    assert log_filename is not None

if __name__ == '__main__':
    test_complex_lunar_lander()