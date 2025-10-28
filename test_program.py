#!/usr/bin/env python3
"""
Test Python script for the program management system.
"""

import sys
import os
from datetime import datetime

def main():
    print("🐍 Hello from Python Program Management!")
    print(f"⏰ Current time: {datetime.now()}")
    print(f"🖥️  Python version: {sys.version}")
    print(f"📁 Current directory: {os.getcwd()}")
    
    # Check if arguments were provided
    if len(sys.argv) > 1:
        print(f"📝 Arguments received: {sys.argv[1:]}")
        for i, arg in enumerate(sys.argv[1:], 1):
            print(f"   Argument {i}: {arg}")
    else:
        print("📝 No arguments provided")
    
    # Simple calculation example
    numbers = [1, 2, 3, 4, 5]
    total = sum(numbers)
    average = total / len(numbers)
    
    print(f"🔢 Numbers: {numbers}")
    print(f"➕ Sum: {total}")
    print(f"📊 Average: {average}")
    
    print("✅ Program execution completed successfully!")

if __name__ == "__main__":
    main()