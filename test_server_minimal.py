#!/usr/bin/env python3
"""Minimal test to isolate the server startup issue."""
import sys
sys.path.insert(0, '/home/tom/Documents/webserver/src')

print("Testing imports...")
try:
    from flask import Flask
    print("✓ Flask")
    from data_store import DataStore
    print("✓ DataStore")
    from program_store import ProgramStore  
    print("✓ ProgramStore")
    
    print("\nInitializing stores...")
    data_store = DataStore()
    print("✓ DataStore initialized")
    program_store = ProgramStore()
    print("✓ ProgramStore initialized")
    
    print("\nTesting program_store methods...")
    programs = program_store.get_program_list()
    print(f"✓ get_program_list() returned {len(programs)} programs")
    
    print("\nAll tests passed! Server should work.")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
