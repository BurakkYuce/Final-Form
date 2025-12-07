"""
Test script to verify AddressBook on-chain
"""
import httpx
import json

# Configuration
SUI_RPC_URL = "https://fullnode.testnet.sui.io:443"
PACKAGE_ID = "0x8e385abb2ccefc0aed625567e72c8005f06ae3a97d534a25cb8e5dd2b62f6f9c"

# Replace with your wallet address
USER_ADDRESS = "0x6d2214052b18cc9ff2f97cb904343a47ab9d85453e45e9477197e75eab365eac"

def get_all_owned_objects(address: str):
    """Get all objects owned by address"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "suix_getOwnedObjects",
        "params": [
            address,
            {
                "options": {
                    "showType": True,
                    "showContent": True,
                    "showOwner": True
                }
            }
        ]
    }

    response = httpx.post(SUI_RPC_URL, json=payload, timeout=10.0)
    return response.json()

def get_address_book_objects(address: str):
    """Get AddressBook objects owned by address"""
    address_book_type = f"{PACKAGE_ID}::address_book::AddressBook"

    print(f"Looking for type: {address_book_type}")

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "suix_getOwnedObjects",
        "params": [
            address,
            {
                "filter": {
                    "StructType": address_book_type
                },
                "options": {
                    "showType": True,
                    "showContent": True,
                    "showOwner": True
                }
            }
        ]
    }

    response = httpx.post(SUI_RPC_URL, json=payload, timeout=10.0)
    return response.json()

if __name__ == "__main__":
    print("=" * 60)
    print(f"Checking AddressBook for: {USER_ADDRESS}")
    print("=" * 60)

    # First get all objects
    print("\n1. Getting ALL owned objects...")
    all_objects = get_all_owned_objects(USER_ADDRESS)

    if "result" in all_objects:
        data = all_objects["result"].get("data", [])
        print(f"   Found {len(data)} objects")

        for obj in data:
            obj_type = obj.get("data", {}).get("type", "unknown")
            obj_id = obj.get("data", {}).get("objectId", "unknown")
            print(f"   - {obj_id[:20]}... : {obj_type[:60]}...")
    else:
        print(f"   Error: {all_objects.get('error')}")

    # Now filter for AddressBook
    print("\n2. Filtering for AddressBook type...")
    address_books = get_address_book_objects(USER_ADDRESS)

    if "result" in address_books:
        data = address_books["result"].get("data", [])
        print(f"   Found {len(data)} AddressBook objects")

        for obj in data:
            obj_data = obj.get("data", {})
            print(f"\n   AddressBook found:")
            print(f"   - Object ID: {obj_data.get('objectId')}")
            print(f"   - Type: {obj_data.get('type')}")
            print(f"   - Content: {json.dumps(obj_data.get('content'), indent=4)}")
    else:
        print(f"   Error: {address_books.get('error')}")

    print("\n" + "=" * 60)
