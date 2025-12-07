# API Testing Guide

Quick reference for testing the Sui Blockchain AI Agent API.

## Base URL

```
http://localhost:8000
```

## Interactive Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Test Endpoints with curl

### 1. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Sui Blockchain AI Agent",
  "version": "1.0.0-mvp"
}
```

### 2. Simple Transfer Intent

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Send 100 SUI to 0xabcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234",
    "user_address": "0x1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234abcd"
  }'
```

### 3. Check Balance

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my SUI balance?",
    "user_address": "0x1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234abcd"
  }'
```

### 4. Ambiguous Intent (Triggers Clarification)

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Send money",
    "user_address": "0x1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234abcd"
  }'
```

Expected response:
```json
{
  "intent": {
    "action": "ambiguous",
    "confidence": 0.5,
    "clarification_needed": true,
    "clarification_question": "How much would you like to send and to whom?"
  },
  "ready_to_execute": false,
  "message": "How much would you like to send and to whom?"
}
```

### 5. Save Contact

```bash
curl -X POST http://localhost:8000/api/v1/contacts/save \
  -H "Content-Type: application/json" \
  -d '{
    "user_address": "0x1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234abcd",
    "contact_name": "Alice",
    "contact_address": "0xabcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234",
    "notes": "My friend Alice"
  }'
```

### 6. List Contacts

```bash
curl "http://localhost:8000/api/v1/contacts/list?user_address=0x1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234abcd"
```

### 7. Transfer to Contact

```bash
# First save contact (step 5), then:
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Send 50 SUI to Alice",
    "user_address": "0x1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234abcd"
  }'
```

### 8. USDC Transfer

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Send 100 USDC to 0xabcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234",
    "user_address": "0x1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234abcd"
  }'
```

## Test with Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Test health
response = requests.get(f"{BASE_URL}/api/v1/health")
print(response.json())

# Test chat
response = requests.post(
    f"{BASE_URL}/api/v1/chat",
    json={
        "message": "Send 100 SUI to 0xabcd...",
        "user_address": "0x1234..."
    }
)
print(response.json())
```

## Test with Postman

Import this collection:

```json
{
  "info": {
    "name": "Sui AI Agent",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/v1/health"
      }
    },
    {
      "name": "Chat - Transfer",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/v1/chat",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\"message\": \"Send 100 SUI to 0xabcd...\", \"user_address\": \"0x1234...\"}"
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    }
  ]
}
```

## Expected Responses

### Successful Transfer Intent

```json
{
  "intent": {
    "action": "transfer_token",
    "confidence": 0.95,
    "parsed_data": {
      "recipient": "0xabcd...",
      "amount": "100000000000",
      "token": "SUI",
      "is_contact_name": false
    },
    "clarification_needed": false,
    "reasoning": "AI identified transfer_token..."
  },
  "dry_run": {
    "action_description": "Transfer 100.0000 SUI to 0xabcd...",
    "recipient": "0xabcd...",
    "amount": "100.0000",
    "token": "SUI",
    "estimated_gas_fee": "0.002000",
    "sender_balance_before": "500.0000",
    "sender_balance_after": "399.9980",
    "risk_level": "low",
    "warnings": []
  },
  "ready_to_execute": true,
  "message": "Ready to transfer 100.0000 SUI. Estimated gas: 0.002000 SUI."
}
```

### Balance Check

```json
{
  "intent": {
    "action": "get_balance",
    "confidence": 0.95,
    "parsed_data": {
      "token": "SUI"
    }
  },
  "dry_run": null,
  "ready_to_execute": false,
  "message": "Your SUI balance is 500.0000"
}
```

## Common Test Scenarios

### Test 1: Strict Mode Validation

Try sending an invalid token (should fail gracefully):
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Send 100 BTC to Alice",
    "user_address": "0x1234..."
  }'
```

AI should ask for clarification since BTC is not in the enum [SUI, USDC].

### Test 2: Contact Privacy

```bash
# Save contact
curl -X POST http://localhost:8000/api/v1/contacts/save \
  -H "Content-Type: application/json" \
  -d '{"user_address": "0x1234...", "contact_name": "Mom", "contact_address": "0xabcd..."}'

# Verify it's encrypted on Walrus
# The blob_id returned contains encrypted data only
```

### Test 3: Disambiguation Flow

```bash
# Step 1: Ambiguous message
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Send to Bob", "user_address": "0x1234..."}'

# Response: "How much would you like to send to Bob?"

# Step 2: Clarify
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "100 SUI", "user_address": "0x1234..."}'
```

## Troubleshooting

### Error: "OPENAI_API_KEY not set"
- Edit `.env` and add your OpenAI API key

### Error: "Failed to connect to Sui RPC"
- Check if Sui testnet is accessible
- Verify `SUI_RPC_URL` in `.env`

### Error: "Walrus upload failed"
- Verify Walrus testnet URLs in `.env`
- Check network connectivity

## Performance Testing

Test response times:

```bash
time curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Send 100 SUI to 0xabcd...", "user_address": "0x1234..."}'
```

Expected: ~1-3 seconds (depends on OpenAI API latency)
