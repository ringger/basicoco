#!/usr/bin/env python3
"""
Test with a minimal BASIC program to see if the issue is with our lunar_lander program
"""

import pexpect
import time

from emulator.config import DEFAULT_PORT

def test_minimal():
    print("🔍 === MINIMAL PROGRAM TEST === 🔍")
    
    child = pexpect.spawn(f'python cli_client.py --host localhost --port {DEFAULT_PORT}',
                         encoding='utf-8', timeout=15)
    
    try:
        print("Connecting...")
        child.expect("READY", timeout=15)
        
        print("Testing simple PRINT statement...")
        child.sendline('10 PRINT "HELLO WORLD"')
        child.expect("READY", timeout=5)
        
        child.sendline("RUN")
        index = child.expect(["HELLO WORLD", "READY", pexpect.TIMEOUT], timeout=5)
        
        if index == 0:
            print("✅ Simple PRINT works!")
        elif index == 1:
            print("❌ Got READY immediately - PRINT didn't work")
        else:
            print("❌ Timeout on simple PRINT")
            
        print(f"Buffer: {repr(child.before)}")
        
        # Try the CLEAR command specifically
        print("\nTesting CLEAR command...")
        child.sendline("NEW")
        child.expect("READY", timeout=5)
        
        child.sendline('10 CLEAR 1000')
        child.expect("READY", timeout=5) 
        
        child.sendline('20 PRINT "AFTER CLEAR"')
        child.expect("READY", timeout=5)
        
        child.sendline("RUN")
        index = child.expect(["AFTER CLEAR", "READY", pexpect.TIMEOUT], timeout=5)
        
        if index == 0:
            print("✅ CLEAR command works!")
        elif index == 1:
            print("❌ CLEAR command causes immediate exit")
        else:
            print("❌ Timeout with CLEAR command")
            
        print(f"Buffer: {repr(child.before)}")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        try:
            child.close()
        except:
            pass

if __name__ == '__main__':
    test_minimal()