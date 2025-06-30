#!/usr/bin/env python3
"""
Simple CLI client for testing HITL functionality
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8001"

def test_hitl_chat():
    """Test the HITL chat functionality"""
    print("🔄 Testing HITL Chat Functionality")
    print("=" * 50)
    
    # Test message that should trigger a tool call
    test_message = "What's the weather like in Paris?"
    
    print(f"Sending: {test_message}")
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": test_message}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get("interrupted"):
            print("\n✅ Successfully interrupted for human approval!")
            print(f"Thread ID: {data['thread_id']}")
            print(f"Interrupt Data: {data['interrupt_data']}")
            
            # Test approval
            print("\n🔄 Testing approval...")
            approval_response = requests.post(
                f"{BASE_URL}/approve",
                json={
                    "action": "approve",
                    "thread_id": data["thread_id"]
                }
            )
            
            if approval_response.status_code == 200:
                approval_data = approval_response.json()
                print(f"Approval Response: {json.dumps(approval_data, indent=2)}")
            else:
                print(f"❌ Approval failed: {approval_response.text}")
        else:
            print("❌ Expected interruption but didn't get one")
    else:
        print(f"❌ Request failed: {response.text}")

def test_rejection():
    """Test rejecting a tool call"""
    print("\n🔄 Testing Tool Rejection")
    print("=" * 50)
    
    test_message = "Search for information about artificial intelligence"
    
    print(f"Sending: {test_message}")
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": test_message}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get("interrupted"):
            print("✅ Successfully interrupted for human approval!")
            
            # Test rejection
            print("\n🔄 Testing rejection...")
            rejection_response = requests.post(
                f"{BASE_URL}/approve",
                json={
                    "action": "reject",
                    "thread_id": data["thread_id"]
                }
            )
            
            if rejection_response.status_code == 200:
                rejection_data = rejection_response.json()
                print(f"Rejection Response: {json.dumps(rejection_data, indent=2)}")
            else:
                print(f"❌ Rejection failed: {rejection_response.text}")
        else:
            print("❌ Expected interruption but didn't get one")
    else:
        print(f"❌ Request failed: {response.text}")

def test_edit():
    """Test editing tool arguments"""
    print("\n🔄 Testing Tool Edit")
    print("=" * 50)
    
    test_message = "What's the weather in NYC?"
    
    print(f"Sending: {test_message}")
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": test_message}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get("interrupted"):
            print("✅ Successfully interrupted for human approval!")
            
            # Test editing
            print("\n🔄 Testing edit (changing NYC to London)...")
            edit_response = requests.post(
                f"{BASE_URL}/approve",
                json={
                    "action": "edit",
                    "edited_args": {"location": "London, UK"},
                    "thread_id": data["thread_id"]
                }
            )
            
            if edit_response.status_code == 200:
                edit_data = edit_response.json()
                print(f"Edit Response: {json.dumps(edit_data, indent=2)}")
            else:
                print(f"❌ Edit failed: {edit_response.text}")
        else:
            print("❌ Expected interruption but didn't get one")
    else:
        print(f"❌ Request failed: {response.text}")

def check_server():
    """Check if the server is running"""
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print("✅ HITL server is running")
            return True
        else:
            print("❌ HITL server returned error")
            return False
    except requests.RequestException:
        print("❌ Cannot connect to HITL server")
        return False

if __name__ == "__main__":
    print("🤖 HITL Functionality Test")
    print("=" * 50)
    
    if not check_server():
        print("Please start the HITL server with: python3 server_hitl.py")
        sys.exit(1)
    
    try:
        test_hitl_chat()
        test_rejection()
        test_edit()
        
        print("\n✅ All HITL tests completed!")
        
    except KeyboardInterrupt:
        print("\n\n👋 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")