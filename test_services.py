"""
Simple test script to verify both services work locally
Run from voiceCoach-master directory
"""
import requests
import json
import time
import sys

# Service URLs
VOICECOACH_URL = "http://localhost:8000"
CHATBOT_URL = "http://localhost:5001"

def test_health_checks():
    """Test health endpoints"""
    print("\n" + "="*60)
    print("Testing Health Checks")
    print("="*60)
    
    # Test VoiceCoach
    try:
        response = requests.get(f"{VOICECOACH_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ VoiceCoach API health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ VoiceCoach API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ VoiceCoach API not reachable: {e}")
        print("   Make sure VoiceCoach is running on port 8000")
        return False
    
    # Test Chatbot
    try:
        response = requests.get(f"{CHATBOT_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Web Chatbot health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Web Chatbot health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Web Chatbot not reachable: {e}")
        print("   Make sure Chatbot is running on port 5001")
        return False
    
    return True


def test_chatbot_auth():
    """Test chatbot authentication"""
    print("\n" + "="*60)
    print("Testing Chatbot Authentication")
    print("="*60)
    
    test_user = {
        "email": f"test_{int(time.time())}@example.com",
        "password": "TestPass123!",
        "name": "Test User"
    }
    
    # Test Signup
    print("\n1. Testing Signup...")
    try:
        response = requests.post(
            f"{CHATBOT_URL}/auth/signup",
            json=test_user,
            timeout=10
        )
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Signup successful")
            print(f"   User: {data.get('user', {}).get('email')}")
            token = data.get('access_token')
            if token:
                print(f"   Token: {token[:20]}...")
            else:
                print("❌ No token returned")
                return False
        else:
            print(f"❌ Signup failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Signup error: {e}")
        return False
    
    # Test Login
    print("\n2. Testing Login...")
    try:
        response = requests.post(
            f"{CHATBOT_URL}/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful")
            token = data.get('access_token')
            if not token:
                print("❌ No token returned")
                return False
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Test Auth Status
    print("\n3. Testing Auth Status...")
    try:
        response = requests.get(
            f"{CHATBOT_URL}/auth/status",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('authenticated'):
                print(f"✅ Auth status check passed")
                print(f"   User: {data.get('user', {}).get('email')}")
            else:
                print("❌ User not authenticated")
                return False
        else:
            print(f"❌ Auth status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Auth status error: {e}")
        return False
    
    return token


def test_chatbot_chat(token):
    """Test chatbot chat functionality"""
    print("\n" + "="*60)
    print("Testing Chatbot Chat")
    print("="*60)
    
    test_message = "My manager gave me feedback and I'm not sure how to respond"
    
    print(f"\nSending message: '{test_message}'")
    
    try:
        response = requests.post(
            f"{CHATBOT_URL}/api/chat",
            json={"message": test_message, "token": token},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data.get('response', '')
            if ai_response:
                print(f"✅ Chat response received")
                print(f"\n   AI Response: {ai_response[:200]}...")
                print(f"\n   Token returned: {data.get('token') is not None}")
                return True
            else:
                print("❌ No response from chatbot")
                return False
        else:
            print(f"❌ Chat request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False


def test_voicecoach_auth():
    """Test VoiceCoach authentication"""
    print("\n" + "="*60)
    print("Testing VoiceCoach Authentication")
    print("="*60)
    
    test_user = {
        "email": f"voicetest_{int(time.time())}@example.com",
        "password": "TestPass123!",
        "name": "Voice Test User"
    }
    
    # Test Signup
    print("\n1. Testing Signup...")
    try:
        response = requests.post(
            f"{VOICECOACH_URL}/auth/signup",
            json=test_user,
            timeout=10
        )
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Signup successful")
            print(f"   User: {data.get('user', {}).get('email')}")
            token = data.get('access_token')
            if token:
                print(f"   Token: {token[:20]}...")
                return True
            else:
                print("❌ No token returned")
                return False
        else:
            print(f"❌ Signup failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Signup error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("VoiceCoach Platform - Local Test Suite")
    print("="*60)
    print("\nThis will test both services are running correctly.")
    print("Make sure both services are started:")
    print("  - VoiceCoach API: http://localhost:8000")
    print("  - Web Chatbot: http://localhost:5001")
    
    input("\nPress Enter to continue...")
    
    # Test health checks
    if not test_health_checks():
        print("\n❌ Health checks failed. Make sure both services are running.")
        sys.exit(1)
    
    # Test chatbot
    token = test_chatbot_auth()
    if not token:
        print("\n❌ Chatbot authentication failed")
        sys.exit(1)
    
    if not test_chatbot_chat(token):
        print("\n❌ Chatbot chat failed")
        sys.exit(1)
    
    # Test VoiceCoach
    if not test_voicecoach_auth():
        print("\n❌ VoiceCoach authentication failed")
        sys.exit(1)
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print("✅ All tests passed!")
    print("\nBoth services are working correctly:")
    print("  ✅ VoiceCoach API health check")
    print("  ✅ VoiceCoach authentication")
    print("  ✅ Web Chatbot health check")
    print("  ✅ Web Chatbot authentication")
    print("  ✅ Web Chatbot chat functionality")
    print("\n🎉 Ready for deployment!")


if __name__ == "__main__":
    main()
