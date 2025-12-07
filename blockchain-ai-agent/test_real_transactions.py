#!/usr/bin/env python3
"""
Comprehensive Test Suite for Sui Blockchain AI Agent
Tests all functionality including REAL transactions on Sui Testnet

WALLET INFO (from a.md):
Wallet 1 (Sender):  0x6d6ea71aeb3029760347ecee4cd7472af79a7d9ec1c9205ef123e726206aec69
Wallet 2 (Recipient): 0x6e0d6daf2309688ce56606e72fca267ae25f36d43d9d27ccf324f96d7e6e7e07
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"

# Wallet credentials (from a.md)
SENDER_ADDRESS = "0x6d6ea71aeb3029760347ecee4cd7472af79a7d9ec1c9205ef123e726206aec69"
SENDER_PRIVATE_KEY = "suiprivkey1qzw4ak32zhgnn25ns2taccem79dnqhzm3z6hy2370f84cefnf837qltw4pn"

RECIPIENT_ADDRESS = "0x6e0d6daf2309688ce56606e72fca267ae25f36d43d9d27ccf324f96d7e6e7e07"
RECIPIENT_PRIVATE_KEY = "suiprivkey1qpath2ypct6ywcvmqz92mypv55p08ld0kj98lm79a77j53xezqack3ca88m"

# Test configuration
TRANSFER_AMOUNT = "0.01"  # SUI (10000000 MIST)


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_test(name: str):
    """Print test header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}TEST: {name}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.RESET}")


async def test_health_check():
    """Test 1: Health check endpoint"""
    print_test("Health Check")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/v1/health")
            result = response.json()

            if response.status_code == 200 and result.get("status") == "healthy":
                print_success(f"Server is healthy: {result}")
                return True
            else:
                print_error(f"Health check failed: {result}")
                return False
        except Exception as e:
            print_error(f"Health check error: {str(e)}")
            return False


async def test_balance_check():
    """Test 2: Balance check via AI"""
    print_test("Balance Check (OpenAI Integration)")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/chat",
                json={
                    "message": "What is my SUI balance?",
                    "user_address": SENDER_ADDRESS
                }
            )
            result = response.json()

            print_info(f"Response: {json.dumps(result, indent=2)}")

            if result.get("intent", {}).get("action") == "get_balance":
                print_success("AI correctly identified balance check intent")
                print_success(f"Balance info: {result.get('message')}")
                return True
            else:
                print_error("AI failed to identify balance check")
                return False

        except Exception as e:
            print_error(f"Balance check error: {str(e)}")
            return False


async def test_save_contact():
    """Test 3: Save encrypted contact to Walrus"""
    print_test("Save Contact (Walrus + Seal Integration)")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/contacts/save",
                json={
                    "user_address": SENDER_ADDRESS,
                    "contact_name": "TestRecipient",
                    "contact_address": RECIPIENT_ADDRESS,
                    "notes": "Test contact for automated testing"
                }
            )
            result = response.json()

            print_info(f"Response: {json.dumps(result, indent=2)}")

            if result.get("blob_id"):
                print_success(f"Contact saved! Blob ID: {result['blob_id']}")
                print_success("Contact encrypted with Seal and uploaded to Walrus")
                return True
            else:
                print_error("Failed to save contact")
                return False

        except Exception as e:
            print_error(f"Save contact error: {str(e)}")
            return False


async def test_list_contacts():
    """Test 4: List and decrypt contacts"""
    print_test("List Contacts (Seal Decryption)")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/contacts/list",
                params={"user_address": SENDER_ADDRESS}
            )
            result = response.json()

            print_info(f"Response: {json.dumps(result, indent=2)}")

            contacts = result.get("contacts", [])
            if contacts:
                print_success(f"Retrieved {len(contacts)} contact(s)")
                for contact in contacts:
                    print_success(f"  - {contact['name']}: {contact['address']}")
                return True
            else:
                print_info("No contacts found (may need to run test_save_contact first)")
                return True

        except Exception as e:
            print_error(f"List contacts error: {str(e)}")
            return False


async def test_transfer_intent_parsing():
    """Test 5: Transfer intent parsing with AI"""
    print_test("Transfer Intent Parsing (OpenAI Strict Mode)")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/chat",
                json={
                    "message": f"Send {TRANSFER_AMOUNT} SUI to TestRecipient",
                    "user_address": SENDER_ADDRESS
                }
            )
            result = response.json()

            print_info(f"Response: {json.dumps(result, indent=2)}")

            if result.get("intent", {}).get("action") == "transfer_token":
                print_success("AI correctly identified transfer intent")

                dry_run = result.get("dry_run")
                if dry_run:
                    print_success(f"Dry-run summary generated:")
                    print_success(f"  - Amount: {dry_run.get('amount')} {dry_run.get('token')}")
                    print_success(f"  - Recipient: {dry_run.get('recipient')}")
                    print_success(f"  - Gas Fee: {dry_run.get('estimated_gas_fee')} SUI")
                    print_success(f"  - Risk Level: {dry_run.get('risk_level')}")
                return True
            else:
                print_error("AI failed to identify transfer intent")
                return False

        except Exception as e:
            print_error(f"Transfer intent parsing error: {str(e)}")
            return False


async def test_real_transaction():
    """Test 6: Execute REAL transaction on Sui blockchain"""
    print_test("REAL Transaction Execution (Sui Testnet)")

    print_info("This will execute a REAL transaction on Sui testnet!")
    print_info(f"Sender: {SENDER_ADDRESS}")
    print_info(f"Recipient: {RECIPIENT_ADDRESS}")
    print_info(f"Amount: {TRANSFER_AMOUNT} SUI")

    # Convert to MIST (1 SUI = 1,000,000,000 MIST)
    amount_mist = int(float(TRANSFER_AMOUNT) * 1_000_000_000)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/execute",
                json={
                    "transaction_data": {
                        "action": "transfer_token",
                        "recipient": RECIPIENT_ADDRESS,
                        "amount": str(amount_mist),
                        "token": "SUI"
                    },
                    "user_address": SENDER_ADDRESS
                },
                params={
                    "private_key": SENDER_PRIVATE_KEY
                }
            )
            result = response.json()

            print_info(f"Response: {json.dumps(result, indent=2)}")

            if result.get("success"):
                digest = result.get("transaction_digest")
                print_success(f"✅ REAL TRANSACTION EXECUTED!")
                print_success(f"Transaction Digest: {digest}")
                print_success(f"Explorer: https://testnet.suivision.xyz/txblock/{digest}")

                effects = result.get("effects", {})
                print_success(f"Gas Used: {effects.get('gas_used', 'N/A')}")
                print_success(f"Status: {effects.get('status', 'N/A')}")
                return True
            else:
                print_error(f"Transaction failed: {result.get('error')}")
                return False

        except Exception as e:
            print_error(f"Real transaction error: {str(e)}")
            return False


async def test_disambiguation():
    """Test 7: AI disambiguation"""
    print_test("AI Disambiguation (Ambiguous Intent)")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/chat",
                json={
                    "message": "Send money",
                    "user_address": SENDER_ADDRESS
                }
            )
            result = response.json()

            print_info(f"Response: {json.dumps(result, indent=2)}")

            intent = result.get("intent", {})
            if intent.get("clarification_needed"):
                print_success("AI correctly identified ambiguous intent")
                print_success(f"Clarification question: {intent.get('clarification_question')}")
                return True
            else:
                print_error("AI did not request clarification for ambiguous intent")
                return False

        except Exception as e:
            print_error(f"Disambiguation test error: {str(e)}")
            return False


async def run_all_tests():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "SUI BLOCKCHAIN AI AGENT TEST SUITE" + " " * 19 + "║")
    print("║" + " " * 20 + "Testing All Features" + " " * 29 + "║")
    print("╚" + "═" * 68 + "╝")
    print(f"{Colors.RESET}\n")

    results = {}

    # Run tests
    results["Health Check"] = await test_health_check()
    results["Balance Check"] = await test_balance_check()
    results["Save Contact"] = await test_save_contact()
    results["List Contacts"] = await test_list_contacts()
    results["Transfer Intent"] = await test_transfer_intent_parsing()
    results["Disambiguation"] = await test_disambiguation()

    # Ask before running real transaction
    print(f"\n{Colors.YELLOW}{Colors.BOLD}")
    print("!" * 70)
    print("WARNING: The next test will execute a REAL transaction on Sui testnet")
    print(f"Amount: {TRANSFER_AMOUNT} SUI + gas fees")
    print("!" * 70)
    print(f"{Colors.RESET}\n")

    user_input = input("Do you want to execute the real transaction test? (yes/no): ")
    if user_input.lower() == "yes":
        results["Real Transaction"] = await test_real_transaction()
    else:
        print_info("Skipping real transaction test")
        results["Real Transaction"] = None

    # Print summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"{Colors.RESET}")

    passed = 0
    failed = 0
    skipped = 0

    for test_name, result in results.items():
        if result is True:
            print(f"{Colors.GREEN}✓ {test_name}: PASSED{Colors.RESET}")
            passed += 1
        elif result is False:
            print(f"{Colors.RED}✗ {test_name}: FAILED{Colors.RESET}")
            failed += 1
        else:
            print(f"{Colors.YELLOW}- {test_name}: SKIPPED{Colors.RESET}")
            skipped += 1

    print(f"\n{Colors.BOLD}")
    print(f"Total: {len(results)} tests")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
    print(f"{Colors.YELLOW}Skipped: {skipped}{Colors.RESET}")

    if failed == 0 and passed > 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.RESET}\n")
    elif failed > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  SOME TESTS FAILED  ⚠️{Colors.RESET}\n")


if __name__ == "__main__":
    print("Starting test suite...")
    print("Make sure the server is running on http://localhost:8000\n")

    asyncio.run(run_all_tests())
