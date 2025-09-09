#!/usr/bin/env python3
"""
Step by step test to debug program execution
"""

import pexpect
import time

def test_step_by_step():
    print("🔍 === STEP BY STEP DEBUG === 🔍")
    
    child = pexpect.spawn('python cli_client.py --host localhost --port 5000', 
                         encoding='utf-8', timeout=20)
    
    try:
        print("\n1. Connecting...")
        child.expect("READY", timeout=15)
        print("   ✅ Connected and got READY prompt")
        
        print("\n2. Loading program...")
        child.sendline('LOAD "lunar_lander"')
        child.expect("READY", timeout=10)
        print("   ✅ Program loaded, got READY prompt")
        
        print("\n3. Trying RUN and immediately checking for ANYTHING...")
        child.sendline("RUN")
        
        # Try to get anything at all
        try:
            index = child.expect([
                "LUNAR LANDER",
                "READY", 
                pexpect.TIMEOUT
            ], timeout=5)
            
            if index == 0:
                print("   ✅ Got 'LUNAR LANDER' output!")
            elif index == 1:
                print("   ❓ Got READY prompt - program finished quickly?")
            else:
                print("   ❌ Timeout - no output detected")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print(f"\n4. Current before buffer: {repr(child.before)}")
        print(f"5. Current after buffer: {repr(child.after)}")
        
        # Try sending CTRL+C to stop any running program
        print("\n6. Sending Ctrl+C...")
        child.sendcontrol('c')
        time.sleep(1)
        
        try:
            child.expect("READY", timeout=5)
            print("   ✅ Got READY after Ctrl+C")
        except:
            print("   ❌ No READY after Ctrl+C")
            
    except Exception as e:
        print(f"❌ Overall error: {e}")
        
    finally:
        try:
            child.close()
        except:
            pass

if __name__ == '__main__':
    test_step_by_step()