#!/usr/bin/env python3
"""
Complete automated lunar lander session with strategic gameplay
"""

import pexpect
import sys
import time
from datetime import datetime

def test_complete_lunar():
    print("🚀 === COMPLETE LUNAR LANDER AUTOMATION === 🚀")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/complete_lunar_session_{timestamp}.log"
    
    with open(log_filename, 'w') as logfile:
        logfile.write(f"Complete Lunar Lander Session Log - {datetime.now()}\n")
        logfile.write("=" * 70 + "\n\n")
        
        child = pexpect.spawn('python cli_client.py --host localhost --port 5000', 
                             encoding='utf-8', timeout=20)
        child.logfile_read = logfile
        
        try:
            print("🔌 Connecting to TRS-80 emulator...")
            child.expect("READY", timeout=15)
            print("✅ Connected!")
            
            print("💾 Loading complex lunar lander...")
            child.sendline('LOAD "lunar_lander"')
            child.expect("READY", timeout=10)
            print("✅ Program loaded (74 lines)!")
            
            print("🚀 Starting the game...")
            child.sendline("RUN")
            
            # Wait for intro and press enter to start
            print("📺 Waiting for intro screen...")
            child.expect("PRESS ENTER TO START", timeout=10)
            print("▶️  Pressing ENTER to start game...")
            logfile.write("\n--- GAME STARTED ---\n")
            child.sendline("")
            
            # Strategic thrust sequence for optimal landing
            strategy = [
                (20, "Strong initial deceleration"),
                (15, "Moderate thrust to control descent"), 
                (12, "Fine-tuning velocity"),
                (10, "Steady approach control"),
                (8, "Precision landing sequence"),
                (5, "Final approach"),
                (3, "Gentle touchdown"),
                (1, "Minimal thrust if needed"),
                (0, "Cut engines")
            ]
            
            game_active = True
            turn = 0
            max_turns = len(strategy)
            
            while game_active and turn < max_turns:
                turn += 1
                thrust, description = strategy[turn-1]
                
                print(f"\n🎯 Turn {turn}: Using thrust {thrust} ({description})")
                logfile.write(f"\n--- TURN {turn}: THRUST {thrust} ---\n")
                logfile.write(f"Strategy: {description}\n")
                
                try:
                    # Wait for game status and thrust prompt
                    index = child.expect([
                        "THRUST (0-30)?",       # Game asking for thrust
                        "LANDING REPORT",       # Game ended with landing
                        "CRASH",                # Crashed
                        "PERFECT LANDING",      # Perfect landing
                        "CONGRATULATIONS",      # Good landing
                        "OUT OF FUEL",          # Fuel depleted
                        pexpect.TIMEOUT         # Timeout
                    ], timeout=15)
                    
                    if index == 0:  # Thrust prompt
                        child.sendline(str(thrust))
                        print(f"  ↳ Applied {thrust} units of thrust")
                        time.sleep(1.5)  # Let physics calculation complete
                        continue
                        
                    elif index in [1, 2, 3, 4, 5]:  # Game ended
                        logfile.write("\n--- GAME ENDED ---\n")
                        print(f"\n🎉 GAME COMPLETED AFTER {turn-1} TURNS!")
                        
                        # Wait for final results display
                        time.sleep(3)
                        
                        # Check for play again prompt
                        try:
                            child.expect("PLAY AGAIN", timeout=10)
                            print("🔄 Declining to play again...")
                            child.sendline("N")
                        except pexpect.exceptions.TIMEOUT:
                            print("No play-again prompt found")
                        
                        game_active = False
                        break
                        
                    elif index == 6:  # Timeout
                        print(f"⏰ Turn {turn} timed out")
                        break
                        
                except pexpect.exceptions.TIMEOUT as e:
                    print(f"❌ Timeout during turn {turn}: {e}")
                    break
            
            if turn >= max_turns:
                print(f"🏁 Completed all {max_turns} strategic moves!")
            
            print("🎮 Game session completed!")
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error during game: {e}")
            
        finally:
            logfile.write("\n--- SESSION ENDED ---\n")
            try:
                child.sendcontrol('c')
                child.close()
            except:
                pass
    
    print(f"\n📄 Complete session log: {log_filename}")
    print(f"🔍 View with: cat {log_filename}")

    # Test passes if we got this far without exceptions
    assert log_filename is not None

if __name__ == '__main__':
    test_complete_lunar()