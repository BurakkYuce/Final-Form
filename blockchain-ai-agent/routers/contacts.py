"""
Contacts Router - On-Chain Contact Management API

This router provides endpoints for managing encrypted contacts stored
on-chain using the AddressBook Move contract.

Flow:
1. User creates an AddressBook (one-time)
2. Contacts are encrypted client-side with Seal encryption
3. Encrypted data is stored on-chain in VecMap
4. User retrieves and decrypts their contacts
"""

import logging
import time
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from services.sui_service import sui_service
from services.seal_service import seal_service
from config import settings

# Configure logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/contacts", tags=["contacts"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateAddressBookRequest(BaseModel):
    """Request to create a new address book for a user"""
    sender_address: str = Field(..., description="User's wallet address")


class CreateAddressBookResponse(BaseModel):
    """Response containing transaction bytes to sign"""
    transaction_bytes: str = Field(..., description="Base64 encoded transaction bytes")
    action: str = "create_address_book"
    message: str = "Sign this transaction to create your address book"


class AddContactRequest(BaseModel):
    """Request to add a new contact"""
    sender_address: str = Field(..., description="User's wallet address")
    address_book_id: str = Field(..., description="User's AddressBook object ID")
    contact_key: str = Field(..., description="Key for the contact (e.g., 'alice', 'mom')")
    contact_name: str = Field(..., description="Display name of the contact")
    contact_address: str = Field(..., description="Contact's wallet address")
    notes: Optional[str] = Field(None, description="Optional notes")
    signature: Optional[str] = Field(None, description="User signature for encryption key derivation")


class AddContactResponse(BaseModel):
    """Response containing transaction bytes for adding contact"""
    transaction_bytes: str = Field(..., description="Base64 encoded transaction bytes")
    contact_key: str = Field(..., description="Contact key")
    action: str = "add_contact"
    message: str = "Sign this transaction to save your contact on-chain"


class GetAddressBookRequest(BaseModel):
    """Request to get user's address book info"""
    user_address: str = Field(..., description="User's wallet address")


class AddressBookInfo(BaseModel):
    """Response with address book information"""
    exists: bool = Field(..., description="Whether the address book exists")
    object_id: Optional[str] = Field(None, description="AddressBook object ID if exists")
    owner: Optional[str] = Field(None, description="Owner address")


class ContactInfo(BaseModel):
    """Decrypted contact information"""
    key: str
    name: str
    address: str
    notes: Optional[str] = None


class ListContactsResponse(BaseModel):
    """Response with list of contacts"""
    contacts: List[ContactInfo]
    count: int


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/address-book/create", response_model=CreateAddressBookResponse)
async def create_address_book(request: CreateAddressBookRequest):
    """
    Create a new on-chain address book for the user.
    
    This is a one-time operation. Each user should have only one AddressBook.
    The transaction must be signed by the user's wallet.
    """
    try:
        logger.info(f"Creating address book for: {request.sender_address}")
        
        # Build the transaction
        tx_result = sui_service.build_create_address_book_tx(
            sender=request.sender_address
        )
        
        # Encode transaction bytes to base64 for frontend
        import base64
        tx_bytes_b64 = base64.b64encode(tx_result["transaction_bytes"]).decode()
        
        return CreateAddressBookResponse(
            transaction_bytes=tx_bytes_b64,
            action=tx_result["action"],
            message="Sign this transaction to create your address book on Sui"
        )
        
    except Exception as e:
        logger.error(f"Error creating address book: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/address-book/info", response_model=AddressBookInfo)
async def get_address_book_info(request: GetAddressBookRequest):
    """
    Check if user has an existing address book and get its info.
    """
    try:
        logger.info(f"Getting address book info for: {request.user_address}")
        
        # Query for address book
        address_book = sui_service.get_user_address_book(request.user_address)
        
        if address_book:
            return AddressBookInfo(
                exists=True,
                object_id=address_book["object_id"],
                owner=address_book["owner"]
            )
        else:
            return AddressBookInfo(
                exists=False,
                object_id=None,
                owner=None
            )
            
    except Exception as e:
        logger.error(f"Error getting address book: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add", response_model=AddContactResponse)
async def add_contact(request: AddContactRequest):
    """
    Add a new encrypted contact to the user's address book.
    
    The contact data is encrypted using Seal before being stored on-chain.
    The transaction must be signed by the user's wallet.
    """
    try:
        logger.info(f"Adding contact '{request.contact_key}' for: {request.sender_address}")
        
        # Step 1: Encrypt contact data using Seal
        encrypted_data = await seal_service.encrypt_contact(
            user_address=request.sender_address,
            name=request.contact_name,
            contact_address=request.contact_address,
            notes=request.notes,
            signature=request.signature
        )
        
        # Generate a nonce (for additional security, we use a timestamp-based nonce)
        import os
        nonce = os.urandom(16)  # 16-byte random nonce
        
        # Current timestamp
        timestamp = int(time.time())
        
        # Step 2: Build the on-chain transaction
        tx_result = sui_service.build_add_contact_tx(
            sender=request.sender_address,
            address_book_id=request.address_book_id,
            contact_key=request.contact_key,
            encrypted_data=encrypted_data,
            nonce=nonce,
            timestamp=timestamp
        )
        
        # Encode transaction bytes to base64
        import base64
        tx_bytes_b64 = base64.b64encode(tx_result["transaction_bytes"]).decode()
        
        return AddContactResponse(
            transaction_bytes=tx_bytes_b64,
            contact_key=request.contact_key,
            action=tx_result["action"],
            message=f"Sign this transaction to save contact '{request.contact_key}' on-chain"
        )
        
    except Exception as e:
        logger.error(f"Error adding contact: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def contacts_health():
    """Health check for contacts service"""
    return {
        "status": "healthy",
        "service": "contacts",
        "package_id": settings.ADDRESS_BOOK_PACKAGE_ID,
        "module": settings.ADDRESS_BOOK_MODULE
    }
