"""
Test the chat API response for create address book
"""
import httpx
import json

API_URL = "http://localhost:8000/api/v1/chat"
USER_ADDRESS = "0x6d2214052b18cc9ff2f97cb904343a47ab9d85453e45e9477197e75eab365eac"

def test_create_address_book():
    payload = {
        "message": "Create my address book",
        "user_address": USER_ADDRESS
    }

    print("Sending request to chat API...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()

    response = httpx.post(API_URL, json=payload, timeout=30.0)

    print(f"Status: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))

    # Check the transaction_data specifically
    data = response.json()
    if "transaction_data" in data:
        print("\n" + "=" * 60)
        print("TRANSACTION DATA:")
        print(json.dumps(data["transaction_data"], indent=2))
        print("=" * 60)

        if data["transaction_data"].get("target"):
            print(f"\nTarget: {data['transaction_data']['target']}")
        else:
            print("\n⚠️ WARNING: No target in transaction_data!")

if __name__ == "__main__":
    test_create_address_book()
