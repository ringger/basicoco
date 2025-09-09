#!/usr/bin/env python3
"""
Very simple test to see what actually happens when we RUN
"""

import pexpect
import time

def simple_test():
    print("🔍 === SIMPLE TEST === 🔍")
    
    child = pexpect.spawn('python cli_client.py --host localhost --port 5000', 
                         encoding='utf-8', timeout=30)
    
    try:
        print("Connecting...")
        child.expect("READY", timeout=15)
        print("Connected!")
        
        print("Loading...")
        child.sendline('LOAD "lunar_lander"')
        child.expect("READY", timeout=10)
        print("Loaded!")
        
        print("Running...")
        child.sendline("RUN")
        
        print("Waiting for ANY output for 5 seconds...")
        time.sleep(5)
        
        print("Current buffer content:")
        print("=" * 50)
        print(repr(child.before))
        print("=" * 50)
        
        # Try to read more
        try:
            child.read_nonblocking(size=1000, timeout=1)
        except:
            pass
            
        print("After read_nonblocking:")
        print("=" * 50) 
        print(repr(child.before))
        print("=" * 50)
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        try:
            child.close()
        except:
            pass

if __name__ == '__main__':
    simple_test()