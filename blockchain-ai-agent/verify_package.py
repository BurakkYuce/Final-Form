"""
Verify the address_book package exists on Sui testnet
"""
import httpx
import json

SUI_RPC_URL = "https://fullnode.testnet.sui.io:443"
PACKAGE_ID = "0x8e385abb2ccefc0aed625567e72c8005f06ae3a97d534a25cb8e5dd2b62f6f9c"

def get_object(object_id: str):
    """Get object by ID"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sui_getObject",
        "params": [
            object_id,
            {
                "showType": True,
                "showContent": True,
                "showOwner": True
            }
        ]
    }

    response = httpx.post(SUI_RPC_URL, json=payload, timeout=10.0)
    return response.json()

def get_normalized_module(package_id: str, module_name: str):
    """Get normalized Move module"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sui_getNormalizedMoveModule",
        "params": [package_id, module_name]
    }

    response = httpx.post(SUI_RPC_URL, json=payload, timeout=10.0)
    return response.json()

if __name__ == "__main__":
    print("=" * 60)
    print(f"Verifying package: {PACKAGE_ID}")
    print("=" * 60)

    # Check if package exists
    print("\n1. Checking if package object exists...")
    result = get_object(PACKAGE_ID)

    if "result" in result:
        data = result["result"].get("data")
        if data:
            print(f"   Package exists!")
            print(f"   Type: {data.get('type')}")
            print(f"   Owner: {data.get('owner')}")
        else:
            error = result["result"].get("error")
            print(f"   Package NOT FOUND: {error}")
    else:
        print(f"   Error: {result.get('error')}")

    # Check for address_book module
    print("\n2. Checking address_book module...")
    module_result = get_normalized_module(PACKAGE_ID, "address_book")

    if "result" in module_result and module_result["result"]:
        print("   Module 'address_book' exists!")
        functions = module_result["result"].get("exposedFunctions", {})
        print(f"   Exposed functions: {list(functions.keys())}")
    else:
        print(f"   Module NOT FOUND: {module_result.get('error')}")

    print("\n" + "=" * 60)
    print("CORRECT TARGET SHOULD BE:")
    print(f"{PACKAGE_ID}::address_book::create_address_book")
    print("=" * 60)
