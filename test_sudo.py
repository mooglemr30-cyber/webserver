#!/usr/bin/env python3
"""Test pexpect sudo functionality"""

import pexpect
import sys

def test_sudo_whoami():
    """Test sudo whoami command"""
    try:
        # Start the sudo command
        child = pexpect.spawn('sudo whoami', timeout=30, encoding='utf-8')
        print(f"Spawned command: sudo whoami")
        
        # Wait for password prompt
        index = child.expect(['.*password.*:', pexpect.EOF, pexpect.TIMEOUT], timeout=5)
        print(f"Expect result index: {index}")
        
        if index == 0:  # Password prompt found
            print("Password prompt detected")
            child.sendline('Casper@0302')
            print("Password sent")
            
            # Wait for command to complete
            try:
                child.expect(pexpect.EOF, timeout=30)
                output = child.before
                exit_code = child.exitstatus if child.exitstatus is not None else 0
                print(f"Command completed with exit code: {exit_code}")
                print(f"Raw output: '{output}'")
                
                # Clean up output
                if output:
                    lines = output.split('\n')
                    filtered_lines = []
                    for line in lines:
                        if not any(keyword in line.lower() for keyword in ['password', '[sudo]']):
                            filtered_lines.append(line)
                    clean_output = '\n'.join(filtered_lines).strip()
                    print(f"Cleaned output: '{clean_output}'")
                    
            except pexpect.TIMEOUT:
                print("Command timed out")
                child.close()
                output = child.before + "\n[Command timed out]"
                exit_code = 124
                
        elif index == 1:  # EOF without password prompt
            print("Command completed without password prompt")
            output = child.before
            exit_code = child.exitstatus if child.exitstatus is not None else 0
            
        else:  # Timeout
            print("Timeout waiting for password prompt")
            child.close()
            output = "[Timeout waiting for password prompt]"
            exit_code = 124
            
        print(f"Final output: '{output}'")
        print(f"Final exit code: {exit_code}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sudo_whoami()