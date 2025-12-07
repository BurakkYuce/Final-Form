"""
Pydantic Models for Request/Response Handling
Defines all data structures for the Sui Blockchain AI Agent API
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class TokenType(str, Enum):
    """Supported token types for transfers"""
    SUI = "SUI"
    USDC = "USDC"


class IntentAction(str, Enum):
    """Possible actions the AI can identify"""
    TRANSFER_TOKEN = "transfer_token"
    RESOLVE_CONTACT = "resolve_contact"
    GET_BALANCE = "get_balance"
    STAKE_TOKEN = "stake_token"
    UNSTAKE_TOKEN = "unstake_token"
    GET_STAKE_INFO = "get_stake_info"
    # Address Book Operations
    CREATE_ADDRESS_BOOK = "create_address_book"
    SAVE_CONTACT = "save_contact"
    LIST_CONTACTS = "list_contacts"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


# ============================================================================
# Request Models
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint - natural language intent"""
    message: str = Field(..., description="Natural language user intent")
    user_address: Optional[str] = Field(None, description="User's Sui wallet address")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Send 100 SUI to Mom",
                    "user_address": "0x1234...",
                    "context": {}
                }
            ]
        }
    }


class ExecuteTransactionRequest(BaseModel):
    """Request model for transaction execution"""
    transaction_data: Dict[str, Any] = Field(..., description="Transaction data from AI parsing")
    user_address: str = Field(..., description="Sender's Sui wallet address")
    signature: Optional[str] = Field(None, description="Transaction signature")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "transaction_data": {
                        "action": "transfer_token",
                        "recipient": "0x5678...",
                        "amount": "100",
                        "token": "SUI"
                    },
                    "user_address": "0x1234..."
                }
            ]
        }
    }


class ContactRequest(BaseModel):
    """Request model for saving/retrieving contacts"""
    user_address: str = Field(..., description="User's wallet address")
    contact_name: Optional[str] = Field(None, description="Contact's display name (e.g., 'Mom')")
    contact_address: Optional[str] = Field(None, description="Contact's wallet address")
    notes: Optional[str] = Field(None, description="Optional notes about the contact")


# ============================================================================
# Response Models
# ============================================================================

class BalanceInfo(BaseModel):
    """Balance information for a token"""
    token: TokenType
    balance: str
    balance_formatted: str


class ContactInfo(BaseModel):
    """Contact information (decrypted)"""
    name: str
    address: str
    notes: Optional[str] = None


class AIIntentResponse(BaseModel):
    """Response from AI intent parsing"""
    action: IntentAction
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence score")
    parsed_data: Optional[Dict[str, Any]] = Field(None, description="Extracted parameters")
    clarification_needed: bool = Field(False, description="Whether user clarification is required")
    clarification_question: Optional[str] = Field(None, description="Question to ask user")
    reasoning: Optional[str] = Field(None, description="AI's reasoning process")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "action": "transfer_token",
                    "confidence": 0.95,
                    "parsed_data": {
                        "recipient": "0x5678...",
                        "amount": "100",
                        "token": "SUI"
                    },
                    "clarification_needed": False,
                    "reasoning": "User wants to send 100 SUI to contact named 'Mom'"
                }
            ]
        }
    }


class DryRunSummary(BaseModel):
    """Dry run summary before transaction execution"""
    action_description: str
    recipient: str
    amount: str
    token: TokenType
    estimated_gas_fee: str
    sender_balance_before: str
    sender_balance_after: str
    risk_level: Literal["low", "medium", "high"]
    warnings: List[str] = Field(default_factory=list)


class TransactionResult(BaseModel):
    """Result of a transaction execution"""
    success: bool
    transaction_digest: Optional[str] = None
    error: Optional[str] = None
    effects: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    intent: AIIntentResponse
    dry_run: Optional[DryRunSummary] = None
    ready_to_execute: bool = False
    message: str = Field(..., description="Human-readable response message")
    transaction_data: Optional[Dict[str, Any]] = Field(None, description="Transaction data for building the PTB on the frontend")


# ============================================================================
# Internal Models (for service communication)
# ============================================================================

class TransferTokenParams(BaseModel):
    """Parameters for token transfer function"""
    recipient: str
    amount: str
    token: TokenType = TokenType.SUI


class ResolveContactParams(BaseModel):
    """Parameters for contact resolution"""
    name: str
    user_address: str


class StakeTokenParams(BaseModel):
    """Parameters for stake token function"""
    amount: str
    token: TokenType = TokenType.SUI


class UnstakeTokenParams(BaseModel):
    """Parameters for unstake token function"""
    amount: str
    token: TokenType = TokenType.SUI


class StakeInfo(BaseModel):
    """Stake information for a user"""
    user_address: str
    staked_amount: str
    staked_amount_formatted: str
    token: TokenType = TokenType.SUI


class EncryptedContactData(BaseModel):
    """Encrypted contact data structure"""
    name: str
    address: str
    notes: Optional[str] = None


class WalrusUploadResponse(BaseModel):
    """Response from Walrus upload"""
    blob_id: str
    size: int
    epochs: int


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
