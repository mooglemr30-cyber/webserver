#!/usr/bin/env python3
"""
AI Bot Chat Program
Connects to https://gpt.ecigdis.co.nz/ai-agent/api/chat.php
Sends text messages in JSON format and displays replies
"""

import requests
import json
import sys
from datetime import datetime

# API Configuration
API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama2"

def print_banner():
    """Print a nice banner for the chat interface"""
    print("\n" + "="*60)
    print("🤖 AI Bot Chat Interface")
    print("="*60)
    print(f"API Endpoint: {API_URL}")
    print("Type 'quit', 'exit', or 'q' to end the conversation")
    print("="*60 + "\n")

def send_message(message, session_id=None, model=MODEL_NAME):
    """
    Send a message to the Ollama API
    
    Args:
        message (str): The message to send
        session_id (str, optional): Not used by Ollama, for compatibility.
        model (str): The Ollama model to use
    """
    payload = {
        "model": model,
        "prompt": message,
        "stream": False
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        response.raise_for_status()
        
        # Extract the response text from the JSON
        response_data = response.json()
        return {
            "success": True,
            "message": response_data.get("response", "No response from model."),
            "session_id": session_id  # Pass through for compatibility
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"API request failed: {e}"
        }

def format_response(response):
    """Format the API response for display"""
    if "error" in response:
        return f"❌ Error: {response['error']}"
    
    # Handle different response formats
    if "reply" in response:
        return f"🤖 Bot: {response['reply']}"
    elif "response" in response:
        return f"🤖 Bot: {response['response']}"
    elif "message" in response:
        return f"🤖 Bot: {response['message']}"
    else:
        # Return the entire response if format is unknown
        return f"🤖 Bot: {json.dumps(response, indent=2)}"

def save_conversation(conversation, filename="conversation_log.txt"):
    """Save the conversation to a file"""
    with open(filename, "a") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Conversation saved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*60}\n")
        for entry in conversation:
            f.write(f"{entry}\n")
        f.write("\n")

def interactive_chat(bot_id=BOT_ID):
    """Run an interactive chat session"""
    print_banner()
    
    print(f"🤖 Connected to Bot ID: {bot_id} (Neural Assistant)\n")
    
    conversation = []
    session_id = None
    
    print("Start chatting! (Type 'quit' to exit)\n")
    
    while True:
        try:
            # Get user input
            user_message = input("You: ").strip()
            
            # Check for exit commands
            if user_message.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye! Saving conversation...")
                if conversation:
                    save_conversation(conversation)
                    print("✅ Conversation saved to conversation_log.txt")
                break
            
            # Skip empty messages
            if not user_message:
                continue
            
            # Record user message
            timestamp = datetime.now().strftime("%H:%M:%S")
            conversation.append(f"[{timestamp}] You: {user_message}")
            
            # Send message to API
            print("⏳ Sending...", end="\r")
            response = send_message(user_message, session_id, bot_id)
            
            # Extract session_id if provided in response
            if "session_id" in response:
                session_id = response["session_id"]
            
            # Format and display response
            formatted_response = format_response(response)
            print(formatted_response)
            conversation.append(f"[{timestamp}] {formatted_response}")
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Saving conversation...")
            if conversation:
                save_conversation(conversation)
                print("✅ Conversation saved to conversation_log.txt")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")

def single_message_mode(message, bot_id=BOT_ID):
    """Send a single message and display the response"""
    print(f"\n📤 Sending message: {message}\n")
    
    response = send_message(message, session_id=None, bot_id=bot_id)
    formatted_response = format_response(response)
    
    print(formatted_response)
    print(f"\n📋 Full Response:\n{json.dumps(response, indent=2)}\n")

def main():
    """Main entry point"""
    # Parse command line arguments
    bot_id = BOT_ID
    message = None
    
    if len(sys.argv) > 1:
        # Check for arguments
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg.startswith("--bot-id="):
                bot_id = int(arg.split("=", 1)[1])
            elif arg.startswith("--message="):
                message = arg.split("=", 1)[1]
            elif arg == "--help" or arg == "-h":
                print("Usage:")
                print(f"  {sys.argv[0]} [--bot-id=1] [--message='Your message']")
                print("\nOptions:")
                print("  --bot-id=ID      : Set the bot ID (default: 1 - Neural Assistant)")
                print("  --message='MSG'  : Send a single message (non-interactive)")
                print("  --help, -h       : Show this help message")
                print("\nExamples:")
                print(f"  {sys.argv[0]}")
                print(f"  {sys.argv[0]} --message='Hello, how are you?'")
                print(f"  {sys.argv[0]} --bot-id=1 --message='Tell me a joke'")
                return
    
    # Run in appropriate mode
    if message:
        single_message_mode(message, bot_id)
    else:
        interactive_chat(bot_id)

if __name__ == "__main__":
    main()
