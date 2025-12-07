# Staking Integration Guide

## 🎉 Overview

The AI Blockchain Agent now supports **SUI staking** with natural language commands! Users can stake and unstake SUI tokens using simple conversational phrases.

## 🚀 Quick Start

### 1. Deploy the Stake Contract

First, deploy the stake contract from `../move/isim/sources/stake.move`:

```bash
cd ../move/isim

# Build the contract
sui move build

# Deploy to testnet
sui client publish --gas-budget 100000000

# Note the outputs:
# - Package ID (e.g., 0xabc123...)
# - StakePool Object ID (e.g., 0xdef456...)
```

### 2. Configure the Backend

Update your `.env` file with the deployed contract information:

```bash
# In blockchain-ai-agent/.env
STAKE_PACKAGE_ID=0xYOUR_PACKAGE_ID_HERE
STAKE_MODULE=stake
STAKE_POOL_OBJECT_ID=0xYOUR_POOL_OBJECT_ID_HERE
```

### 3. Start the Backend

```bash
cd blockchain-ai-agent
python main.py
```

The server will start at `http://localhost:8000`

## 📖 Natural Language Commands

### Stake SUI

**User says:**
```
"Stake 100 SUI"
"Lock 50 SUI in staking"
"I want to stake 200 SUI"
```

**What happens:**
1. AI parses the intent
2. Backend checks your balance
3. Generates a dry-run summary showing:
   - Amount to stake
   - Gas fee
   - Balance before/after
   - Risk level
4. You confirm by calling `/execute` with your private key

### Unstake SUI

**User says:**
```
"Unstake 50 SUI"
"Withdraw 100 from staking"
"Get back 75 SUI from stake pool"
```

**What happens:**
1. AI parses the intent
2. Backend checks your current stake
3. Validates you have enough staked
4. Generates dry-run summary
5. You confirm by calling `/execute`

### Check Stake Info

**User says:**
```
"How much have I staked?"
"What's my stake balance?"
"Show my staking info"
```

**What happens:**
1. AI calls the stake contract's view function
2. Returns your staked amount immediately
3. No transaction needed (read-only)

## 🔧 API Examples

### Example 1: Stake 100 SUI

```bash
# Step 1: Parse intent and get dry-run
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Stake 100 SUI",
    "user_address": "0x1234..."
  }'

# Response:
{
  "intent": {
    "action": "stake_token",
    "confidence": 0.95,
    "parsed_data": {
      "amount": "100",
      "token": "SUI"
    }
  },
  "dry_run": {
    "action_description": "Transfer 100.0000 SUI to Staking Pool",
    "estimated_gas_fee": "0.002000 SUI",
    "sender_balance_before": "500.0000 SUI",
    "sender_balance_after": "399.9980 SUI",
    "risk_level": "low"
  },
  "ready_to_execute": true,
  "transaction_data": {
    "action": "stake_token",
    "amount": "100000000000",
    "token": "SUI"
  }
}

# Step 2: Execute the transaction
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_address": "0x1234...",
    "transaction_data": {
      "action": "stake_token",
      "amount": "100000000000",
      "token": "SUI",
      "private_key": "suiprivkey1q..."
    }
  }'

# Response:
{
  "success": true,
  "transaction_digest": "ABC123...",
  "effects": {...}
}
```

### Example 2: Check Stake Info

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How much have I staked?",
    "user_address": "0x1234..."
  }'

# Response:
{
  "intent": {
    "action": "get_stake_info",
    "confidence": 0.95
  },
  "message": "You have staked 100.0000 SUI in the staking pool."
}
```

### Example 3: Unstake 50 SUI

```bash
# Step 1: Parse intent
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Withdraw 50 SUI from staking",
    "user_address": "0x1234..."
  }'

# Step 2: Execute (if dry-run looks good)
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_address": "0x1234...",
    "transaction_data": {
      "action": "unstake_token",
      "amount": "50000000000",
      "token": "SUI",
      "private_key": "suiprivkey1q..."
    }
  }'
```

## 🏗️ Architecture

### Smart Contract (`stake.move`)

```move
module pkg::stake {
    public struct StakePool has key, store {
        id: UID,
        balance: Balance<SUI>,
        stakes: Table<address, u64>
    }

    public entry fun stake(pool: &mut StakePool, payment: Coin<SUI>, ctx: &mut TxContext)
    public entry fun unstake(pool: &mut StakePool, amount: u64, ctx: &mut TxContext)
    public fun get_user_stake(pool: &StakePool, user: address): u64
}
```

### Backend Integration

1. **OpenAI Service** (`openai_service.py`)
   - Added 3 new tools: `stake_token`, `unstake_token`, `get_stake_info`
   - AI parses natural language into function calls

2. **Sui Service** (`sui_service.py`)
   - `get_user_stake()`: Reads from contract using devInspect
   - `build_stake_transaction()`: Creates PTB for staking
   - `build_unstake_transaction()`: Creates PTB for unstaking

3. **Chat Router** (`chat.py`)
   - Handles 3 new actions: `STAKE_TOKEN`, `UNSTAKE_TOKEN`, `GET_STAKE_INFO`
   - Validates balances and stake amounts
   - Generates dry-run summaries

## 🔒 Security

- **Dry-Run Validation**: Always shows balance impact before execution
- **Stake Verification**: Checks you have enough staked before unstaking
- **Balance Checks**: Prevents staking more than you have
- **Gas Estimation**: Shows transaction costs upfront

## 🎯 Use Cases

1. **Passive Income**: Stake SUI to earn rewards
2. **Long-term Holding**: Lock tokens safely
3. **Flexible Withdrawals**: Unstake anytime
4. **Easy Management**: Natural language interface

## 📝 Example Conversation

```
User: "Hey, how much SUI do I have?"
AI: "Your SUI balance is 1000.0000"

User: "Stake 500 SUI"
AI: "Ready to stake 500 SUI. Estimated gas: 0.002 SUI.
     Balance after: 499.9980 SUI. Add your private_key and call /execute."

User: [Calls /execute with private_key]
AI: "Stake SUCCESS! Digest: ABC123..."

User: "How much did I stake?"
AI: "You have staked 500.0000 SUI in the staking pool."

User: "Withdraw 200 from staking"
AI: "Ready to unstake 200 SUI. Add your private_key and call /execute."

User: [Calls /execute with private_key]
AI: "Unstake SUCCESS! Digest: DEF456..."
```

## 🚧 Limitations

- Currently only SUI is supported for staking
- No rewards calculation (add this in future versions)
- Stake contract must be deployed manually
- MVP uses simplified gas estimation

## 🔮 Future Enhancements

1. **Rewards Tracking**: Show accumulated rewards
2. **Auto-Compounding**: Automatically restake rewards
3. **Multiple Pools**: Support different staking pools
4. **Time Locks**: Add optional lock periods
5. **APY Display**: Show current staking APY

## 🎉 Summary

You now have a fully integrated staking system with natural language control! Users can:
- ✅ Stake SUI with "Stake 100 SUI"
- ✅ Unstake with "Withdraw 50 from staking"
- ✅ Check balance with "How much have I staked?"
- ✅ All with AI-powered safety checks

Enjoy your AI-powered staking experience! 🚀
