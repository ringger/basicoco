#!/usr/bin/env python3
"""
Use pexpect to drive the CLI client interactively and show real usage
"""

import pexpect
import sys
import time

from emulator.config import DEFAULT_PORT

def test_cli_session():
    print("=== STARTING TRS-80 CLI SESSION ===")
    print("Connecting to backend server...")
    
    # Start the CLI client
    child = pexpect.spawn(f'python cli_client.py --host localhost --port {DEFAULT_PORT}',
                         encoding='utf-8', timeout=10)
    
    # Show all output
    child.logfile_read = sys.stdout
    
    try:
        # Wait for connection
        print("\n--- Waiting for connection ---")
        child.expect("READY", timeout=15)
        
        # Test new FILES command
        print("\n--- Testing FILES command ---")
        child.sendline("FILES")
        child.expect("READY", timeout=10)
        
        # Load our lunar lander program
        print("\n--- Loading simple_lunar program ---")
        child.sendline('LOAD "simple_lunar"')
        child.expect("READY", timeout=10)
        
        # Show first few lines of the program
        print("\n--- Showing program listing ---")
        child.sendline("LIST")
        child.expect("READY", timeout=10)
        
        # Run the game!
        print("\n--- Starting the game ---")
        child.sendline("RUN")
        
        # Wait for initial game display
        child.expect("FUEL:", timeout=10)
        
        # Play the game with different thrust values
        thrust_values = [15, 12, 8, 5, 2, 0]
        
        for i, thrust in enumerate(thrust_values):
            print(f"\n--- Turn {i+1}: Using thrust {thrust} ---")
            try:
                child.expect("THRUST", timeout=10)
                child.sendline(str(thrust))
                time.sleep(1)  # Give time to process
                
                # Check if we've landed
                index = child.expect(["LANDED!", "ALTITUDE:", pexpect.TIMEOUT], timeout=5)
                if index == 0:  # LANDED!
                    print("\n🚀 GAME COMPLETED! 🚀")
                    break
                elif index == 2:  # TIMEOUT
                    print("Turn timeout - continuing...")
                    continue
                    
            except pexpect.exceptions.TIMEOUT:
                print(f"Timeout on turn {i+1}")
                break
        
        # Wait a moment for final output
        time.sleep(2)
        
        print("\n=== CLI SESSION DEMONSTRATION COMPLETE ===")
        
    except pexpect.exceptions.TIMEOUT as e:
        print(f"\nTimeout occurred: {e}")
        print("Current buffer:", child.before)
        
    except pexpect.exceptions.EOF:
        print("\nCLI session ended")
        
    finally:
        # Clean exit
        try:
            child.sendcontrol('c')  # Ctrl+C
            child.close()
        except:
            pass

if __name__ == '__main__':
    test_cli_session()