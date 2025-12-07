# Sui Blockchain AI Agent - MVP Backend

An AI-powered blockchain agent that parses natural language intents and executes them on the Sui blockchain with **privacy-first** contact management.

## 🎯 Features

- **Natural Language Processing**: Parse user intents like "Send 100 SUI to Mom" using OpenAI GPT-4
- **Strict Mode Function Calling**: Guaranteed valid JSON outputs with type-safe parameters
- **Privacy-First Architecture**: Encrypted contact storage using Seal + Walrus
- **Programmable Transaction Blocks (PTB)**: Build complex Sui transactions
- **Dry-Run Summaries**: Transaction safety checks before execution
- **Multi-Token Support**: SUI and USDC transfers
- **Staking Integration**: Stake and unstake SUI tokens with natural language commands

## 🏗️ Architecture

```
┌─────────────────┐
│   User Input    │  "Send 100 SUI to Mom"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  OpenAI GPT-4   │  Parse intent with strict mode
│  (Strict Mode)  │  → transfer_token(recipient="Mom", amount="100", token="SUI")
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Contact Resolver│  Mom → 0x1234...
│  (Seal + Walrus)│  Privacy: Encrypted storage
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Sui Service    │  Build PTB transaction
│      (PTB)      │  Estimate gas, check balance
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Dry-Run Summary│  Show user: amount, gas, risk
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Execute      │  Sign & send to Sui blockchain
└─────────────────┘
```

## 📦 Technology Stack

- **Language**: Python 3.12+
- **Framework**: FastAPI (Async)
- **AI**: OpenAI API (gpt-4o-2024-08-06)
- **Blockchain**: pysui (Sui Python SDK)
- **Storage**: Walrus (Decentralized blob storage)
- **Encryption**: cryptography (Fernet)
- **Database**: In-memory (MVP) / SQLite (production-ready)

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.12+
- OpenAI API key
- Sui wallet (testnet)

### 2. Installation

```bash
# Clone the repository
cd blockchain-ai-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# The file already contains testnet configuration
```

**Important**: Make sure to add your OpenAI API key in `.env`:
```
OPENAI_API_KEY=sk-proj-your-key-here
```

### 4. Run the Server

```bash
# From blockchain-ai-agent directory
python main.py
```

The server will start at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

## 📖 API Endpoints

### 1. Chat Endpoint (Intent Parsing)

**POST** `/api/v1/chat`

Parse natural language and get dry-run summary.

```json
{
  "message": "Send 100 SUI to Mom",
  "user_address": "0x1234...",
  "context": {}
}
```

**Response:**
```json
{
  "intent": {
    "action": "transfer_token",
    "confidence": 0.95,
    "parsed_data": {
      "recipient": "0x5678...",
      "amount": "100000000000",
      "token": "SUI"
    },
    "clarification_needed": false
  },
  "dry_run": {
    "action_description": "Transfer 100.0000 SUI to Mom",
    "estimated_gas_fee": "0.002000 SUI",
    "sender_balance_before": "500.0000 SUI",
    "sender_balance_after": "399.9980 SUI",
    "risk_level": "low",
    "warnings": []
  },
  "ready_to_execute": true,
  "message": "Ready to transfer 100.0000 SUI to Mom. Estimated gas: 0.002000 SUI."
}
```

### 2. Execute Transaction

**POST** `/api/v1/execute`

Execute a prepared transaction.

```json
{
  "transaction_data": {
    "action": "transfer_token",
    "recipient": "0x5678...",
    "amount": "100000000000",
    "token": "SUI"
  },
  "user_address": "0x1234..."
}
```

### 3. Save Contact (Encrypted)

**POST** `/api/v1/contacts/save`

Save encrypted contact to Walrus.

```json
{
  "user_address": "0x1234...",
  "contact_name": "Mom",
  "contact_address": "0x5678...",
  "notes": "My mother's wallet"
}
```

### 4. List Contacts

**GET** `/api/v1/contacts/list?user_address=0x1234...`

Retrieve and decrypt all contacts.

### 5. Health Check

**GET** `/api/v1/health`

## 🔒 Privacy-First Contact Management

### How It Works

1. **Encryption (Seal Service)**:
   ```
   Contact Data → Encrypt with user signature → Encrypted Blob
   ```

2. **Storage (Walrus Service)**:
   ```
   Encrypted Blob → Upload to Walrus → blob_id
   ```

3. **Reference Storage**:
   ```
   user_address → blob_id (in-memory or on-chain)
   ```

4. **Retrieval**:
   ```
   blob_id → Download from Walrus → Decrypt with signature → Contact Data
   ```

**Privacy Guarantees**:
- ✅ Contact names NEVER stored in plaintext
- ✅ Only user with correct signature can decrypt
- ✅ Walrus data is public but encrypted
- ✅ No central authority can read contacts

## 🧪 Example Usage

### Example 1: Simple Transfer

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Send 50 SUI to 0xabcd1234...",
    "user_address": "0x1234..."
  }'
```

### Example 2: Transfer to Contact

```bash
# First, save contact
curl -X POST http://localhost:8000/api/v1/contacts/save \
  -H "Content-Type: application/json" \
  -d '{
    "user_address": "0x1234...",
    "contact_name": "Alice",
    "contact_address": "0xabcd..."
  }'

# Then transfer
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Send 100 SUI to Alice",
    "user_address": "0x1234..."
  }'
```

### Example 3: Check Balance

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my SUI balance?",
    "user_address": "0x1234..."
  }'
```

### Example 4: Stake SUI

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Stake 100 SUI",
    "user_address": "0x1234..."
  }'
```

### Example 5: Unstake SUI

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Withdraw 50 SUI from staking",
    "user_address": "0x1234..."
  }'
```

### Example 6: Check Stake Info

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How much have I staked?",
    "user_address": "0x1234..."
  }'
```

## 📂 Project Structure

```
blockchain-ai-agent/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (gitignored)
├── .env.example          # Example configuration
├── models/
│   ├── __init__.py
│   └── schemas.py        # Pydantic models
├── services/
│   ├── __init__.py
│   ├── openai_service.py  # AI intelligence layer
│   ├── sui_service.py     # Blockchain interaction
│   ├── walrus_service.py  # Decentralized storage
│   └── seal_service.py    # Encryption service
└── routers/
    ├── __init__.py
    └── chat.py           # API endpoints
```

## 🔧 Configuration Options

All configuration is in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `OPENAI_MODEL` | Model to use | `gpt-4o-2024-08-06` |
| `SUI_NETWORK` | Sui network | `testnet` |
| `SUI_RPC_URL` | Sui RPC endpoint | Testnet URL |
| `STAKE_PACKAGE_ID` | Deployed stake contract package ID | `0x0` (update after deployment) |
| `STAKE_MODULE` | Stake contract module name | `stake` |
| `STAKE_POOL_OBJECT_ID` | Shared StakePool object ID | `0x0` (update after deployment) |
| `WALRUS_PUBLISHER_URL` | Walrus publisher | Testnet URL |
| `WALRUS_AGGREGATOR_URL` | Walrus aggregator | Testnet URL |
| `API_HOST` | Server host | `0.0.0.0` |
| `API_PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `True` |
| `SECRET_KEY` | Encryption salt | Random string |

## 🎯 Implementation Notes

### OpenAI Strict Mode

The AI service uses **strict mode** for function calling:

```python
{
  "type": "function",
  "function": {
    "name": "transfer_token",
    "strict": True,  # CRITICAL: Guarantees schema compliance
    "parameters": {
      "type": "object",
      "properties": {
        "token": {
          "type": "string",
          "enum": ["SUI", "USDC"]  # Prevents hallucinations
        }
      }
    }
  }
}
```

**Benefits**:
- ✅ Guaranteed valid JSON
- ✅ Type-safe outputs
- ✅ No hallucinated token names
- ✅ Reliable blockchain operations

### Disambiguation Handling

When user intent is unclear:

```
User: "Send money"
AI: "How much would you like to send and to whom?"

User: "Send to Alice"
AI: "How much would you like to send to Alice?"
```

### Dry-Run Safety

Before execution, users see:
- Action description
- Recipient address
- Amount and token
- Gas fee estimate
- Balance before/after
- Risk level (low/medium/high)
- Warnings (if any)

## 🚧 MVP Limitations

This is an MVP implementation. Production considerations:

1. **Wallet Integration**: Currently simulated, needs real wallet signing
2. **Contact Storage**: In-memory, should use SQLite or on-chain
3. **Error Handling**: Basic, needs comprehensive error recovery
4. **Gas Estimation**: Simplified, should use dry_run_transaction_block
5. **Multi-Sig**: Not implemented
6. **Rate Limiting**: Not implemented
7. **Authentication**: Not implemented

## 📚 Documentation References

- **Sui Docs**: https://docs.sui.io
- **Walrus Docs**: https://docs.walrus.site
- **OpenAI Docs**: https://platform.openai.com/docs
- **pysui**: https://github.com/FrankC01/pysui

## 🤝 Contributing

This is an MVP for hackathon purposes. For production use:
1. Add comprehensive tests
2. Implement proper wallet integration
3. Add database persistence
4. Implement authentication/authorization
5. Add rate limiting
6. Improve error handling

## 📄 License

MIT License

## 🙏 Acknowledgments

- Sui Foundation for blockchain infrastructure
- Mysten Labs for Walrus and Seal
- OpenAI for GPT-4 API
- FastAPI for the excellent framework
