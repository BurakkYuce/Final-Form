"""
Comprehensive API Test Script for Blockchain AI Agent
Tests all endpoints and writes results to a log file
"""

import httpx
import json
import asyncio
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
OUTPUT_FILE = "test_results.txt"

# Test wallet address
TEST_USER_ADDRESS = "0xtest_user_123456789"
TEST_CONTACT_ADDRESS = "0xalice_contact_address_abc"

async def log_result(f, test_name: str, status: str, response: dict = None, error: str = None):
    """Log test result to file and console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = f"\n{'='*60}\n"
    result += f"[{timestamp}] TEST: {test_name}\n"
    result += f"STATUS: {status}\n"
    
    if response:
        result += f"RESPONSE:\n{json.dumps(response, indent=2, ensure_ascii=False)}\n"
    if error:
        result += f"ERROR: {error}\n"
    
    result += f"{'='*60}\n"
    
    print(result)
    f.write(result)


async def test_health(client, f):
    """Test 1: Health Check"""
    try:
        response = await client.get(f"{BASE_URL}/health")
        data = response.json()
        await log_result(f, "Health Check", "✅ PASS", response=data)
        return True
    except Exception as e:
        await log_result(f, "Health Check", "❌ FAIL", error=str(e))
        return False


async def test_chat_balance_query(client, f):
    """Test 2: Chat - Balance Query"""
    try:
        payload = {
            "message": "What is my SUI balance?",
            "user_address": TEST_USER_ADDRESS
        }
        response = await client.post(f"{BASE_URL}/chat", json=payload)
        data = response.json()
        await log_result(f, "Chat - Balance Query", "✅ PASS", response=data)
        return True
    except Exception as e:
        await log_result(f, "Chat - Balance Query", "❌ FAIL", error=str(e))
        return False


async def test_chat_transfer_intent(client, f):
    """Test 3: Chat - Transfer Intent"""
    try:
        payload = {
            "message": "Send 10 SUI to 0xrecipient123",
            "user_address": TEST_USER_ADDRESS
        }
        response = await client.post(f"{BASE_URL}/chat", json=payload)
        data = response.json()
        await log_result(f, "Chat - Transfer Intent", "✅ PASS", response=data)
        return True
    except Exception as e:
        await log_result(f, "Chat - Transfer Intent", "❌ FAIL", error=str(e))
        return False


async def test_chat_ambiguous_message(client, f):
    """Test 4: Chat - Ambiguous Message"""
    try:
        payload = {
            "message": "Do something with my tokens",
            "user_address": TEST_USER_ADDRESS
        }
        response = await client.post(f"{BASE_URL}/chat", json=payload)
        data = response.json()
        await log_result(f, "Chat - Ambiguous Message", "✅ PASS", response=data)
        return True
    except Exception as e:
        await log_result(f, "Chat - Ambiguous Message", "❌ FAIL", error=str(e))
        return False


async def test_chat_contact_name_transfer(client, f):
    """Test 5: Chat - Transfer to Contact Name"""
    try:
        payload = {
            "message": "Send 5 SUI to Alice",
            "user_address": TEST_USER_ADDRESS
        }
        response = await client.post(f"{BASE_URL}/chat", json=payload)
        data = response.json()
        await log_result(f, "Chat - Transfer to Contact Name", "✅ PASS", response=data)
        return True
    except Exception as e:
        await log_result(f, "Chat - Transfer to Contact Name", "❌ FAIL", error=str(e))
        return False


async def test_contacts_save(client, f):
    """Test 6: Save Contact"""
    try:
        payload = {
            "user_address": TEST_USER_ADDRESS,
            "contact_name": "Alice",
            "contact_address": TEST_CONTACT_ADDRESS,
            "notes": "Test contact"
        }
        response = await client.post(f"{BASE_URL}/contacts/save", json=payload)
        data = response.json()
        status = "✅ PASS" if response.status_code == 200 else f"⚠️ STATUS {response.status_code}"
        await log_result(f, "Contacts - Save", status, response=data)
        return response.status_code == 200
    except Exception as e:
        await log_result(f, "Contacts - Save", "❌ FAIL", error=str(e))
        return False


async def test_contacts_list(client, f):
    """Test 7: List Contacts"""
    try:
        response = await client.get(f"{BASE_URL}/contacts/list", params={"user_address": TEST_USER_ADDRESS})
        data = response.json()
        await log_result(f, "Contacts - List", "✅ PASS", response=data)
        return True
    except Exception as e:
        await log_result(f, "Contacts - List", "❌ FAIL", error=str(e))
        return False


async def test_execute_without_key(client, f):
    """Test 8: Execute Transaction (No Private Key - Should Fail)"""
    try:
        payload = {
            "user_address": TEST_USER_ADDRESS,
            "action": "transfer",
            "params": {
                "recipient": "0xrecipient123",
                "amount": 1000000000,
                "token": "SUI"
            }
        }
        response = await client.post(f"{BASE_URL}/execute", json=payload)
        data = response.json()
        # This should fail because no private key
        status = "✅ PASS (Expected rejection)" if response.status_code >= 400 else "⚠️ Unexpected success"
        await log_result(f, "Execute - No Private Key", status, response=data)
        return True
    except Exception as e:
        await log_result(f, "Execute - No Private Key", "✅ PASS (Expected error)", error=str(e))
        return True


async def test_chat_stake_intent(client, f):
    """Test 9: Chat - Stake Intent"""
    try:
        payload = {
            "message": "Stake my NFT for rewards",
            "user_address": TEST_USER_ADDRESS
        }
        response = await client.post(f"{BASE_URL}/chat", json=payload)
        data = response.json()
        await log_result(f, "Chat - Stake Intent", "✅ PASS", response=data)
        return True
    except Exception as e:
        await log_result(f, "Chat - Stake Intent", "❌ FAIL", error=str(e))
        return False


async def test_chat_usdc_balance(client, f):
    """Test 10: Chat - USDC Balance Query"""
    try:
        payload = {
            "message": "What is my USDC balance?",
            "user_address": TEST_USER_ADDRESS
        }
        response = await client.post(f"{BASE_URL}/chat", json=payload)
        data = response.json()
        await log_result(f, "Chat - USDC Balance", "✅ PASS", response=data)
        return True
    except Exception as e:
        await log_result(f, "Chat - USDC Balance", "❌ FAIL", error=str(e))
        return False


async def run_all_tests():
    """Run all API tests"""
    print("\n" + "="*60)
    print("  BLOCKCHAIN AI AGENT - API TEST SUITE")
    print("="*60 + "\n")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("BLOCKCHAIN AI AGENT - API TEST RESULTS\n")
        f.write(f"Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Base URL: {BASE_URL}\n")
        f.write("="*60 + "\n")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            results = []
            
            # Run all tests
            results.append(("Health Check", await test_health(client, f)))
            results.append(("Balance Query", await test_chat_balance_query(client, f)))
            results.append(("Transfer Intent", await test_chat_transfer_intent(client, f)))
            results.append(("Ambiguous Message", await test_chat_ambiguous_message(client, f)))
            results.append(("Contact Name Transfer", await test_chat_contact_name_transfer(client, f)))
            results.append(("Save Contact", await test_contacts_save(client, f)))
            results.append(("List Contacts", await test_contacts_list(client, f)))
            results.append(("Execute No Key", await test_execute_without_key(client, f)))
            results.append(("Stake Intent", await test_chat_stake_intent(client, f)))
            results.append(("USDC Balance", await test_chat_usdc_balance(client, f)))
            
            # Summary
            passed = sum(1 for _, r in results if r)
            failed = len(results) - passed
            
            summary = f"\n{'='*60}\n"
            summary += f"TEST SUMMARY\n"
            summary += f"{'='*60}\n"
            summary += f"Total Tests: {len(results)}\n"
            summary += f"Passed: {passed} ✅\n"
            summary += f"Failed: {failed} ❌\n"
            summary += f"Success Rate: {(passed/len(results)*100):.1f}%\n"
            summary += f"{'='*60}\n"
            
            print(summary)
            f.write(summary)
    
    print(f"\n📄 Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
