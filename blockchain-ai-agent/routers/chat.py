"""
Chat Router - Main API endpoints for AI Agent interaction

Provides endpoints for:
1. /chat - Parse natural language intents and return dry-run summaries
2. /execute - Execute blockchain transactions
3. /contacts - Manage encrypted contact book
"""

import logging
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

# Configure logger for this module
logger = logging.getLogger(__name__)

from models.schemas import (
    ChatRequest,
    ChatResponse,
    ExecuteTransactionRequest,
    TransactionResult,
    ContactRequest,
    ContactInfo,
    IntentAction,
    TokenType,
    ErrorResponse
)
from services import (
    openai_service,
    sui_service,
    walrus_service,
    seal_service
)

# Create router
router = APIRouter(prefix="/api/v1", tags=["AI Agent"])


# ============================================================================
# In-Memory Contact Storage (MVP)
# In production, use SQLite or on-chain storage
# ============================================================================
# Structure: {user_address: blob_id}
contact_storage: Dict[str, str] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Parse natural language intent and prepare transaction

    Flow:
    1. AI parses user message using OpenAI with strict mode
    2. If contact name is used, resolve to wallet address
    3. If transfer action, get balance and generate dry-run summary
    4. Return intent + dry-run for user confirmation

    Example requests:
    - "Send 100 SUI to Mom"
    - "What's my USDC balance?"
    - "Transfer 50 USDC to 0x1234..."
    """
    logger.info(f"=== Chat Request Received ===")
    logger.info(f"Message: {request.message}")
    logger.info(f"User Address: {request.user_address}")
    logger.debug(f"Context: {request.context}")
    
    try:
        # Step 1: Parse intent using OpenAI
        logger.info("Step 1: Parsing intent using OpenAI...")
        intent = await openai_service.parse_intent(
            message=request.message,
            user_context={"user_address": request.user_address}
        )
        logger.info(f"Intent parsed: action={intent.action}, confidence={intent.confidence}")
        logger.debug(f"Parsed data: {intent.parsed_data}")

        # Step 2: Handle different action types
        if intent.action == IntentAction.AMBIGUOUS:
            # AI needs clarification
            logger.info("Intent is AMBIGUOUS, requesting clarification")
            return ChatResponse(
                intent=intent,
                dry_run=None,
                ready_to_execute=False,
                message=intent.clarification_question or "Could you provide more details?"
            )

        elif intent.action == IntentAction.GET_BALANCE:
            # Get balance
            logger.info("Handling GET_BALANCE action")
            if not request.user_address:
                logger.warning("Balance query failed: no user address provided")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User address required for balance query"
                )

            token_type = TokenType(intent.parsed_data.get("token", "SUI"))
            logger.info(f"Fetching {token_type.value} balance for {request.user_address}")
            balance_info = await sui_service.get_balance(
                address=request.user_address,
                token_type=token_type
            )
            logger.info(f"Balance retrieved: {balance_info.balance_formatted} {token_type.value}")

            return ChatResponse(
                intent=intent,
                dry_run=None,
                ready_to_execute=False,
                message=f"Your {balance_info.token.value} balance is {balance_info.balance_formatted}"
            )

        elif intent.action == IntentAction.GET_STAKE_INFO:
            # Get stake info
            logger.info("Handling GET_STAKE_INFO action")
            if not request.user_address:
                logger.warning("Stake info query failed: no user address provided")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User address required for stake info query"
                )

            token_type = TokenType(intent.parsed_data.get("token", "SUI"))
            logger.info(f"Fetching {token_type.value} stake info for {request.user_address}")
            stake_info = await sui_service.get_user_stake(
                user_address=request.user_address,
                token_type=token_type
            )
            logger.info(f"Stake info retrieved: {stake_info.staked_amount_formatted} {token_type.value}")

            return ChatResponse(
                intent=intent,
                dry_run=None,
                ready_to_execute=False,
                message=f"You have staked {stake_info.staked_amount_formatted} {stake_info.token.value} in the staking pool."
            )

        elif intent.action == IntentAction.STAKE_TOKEN:
            # Handle stake
            logger.info("Handling STAKE_TOKEN action")
            if not request.user_address:
                logger.warning("Stake failed: no user address provided")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User address required for staking"
                )

            parsed_data = intent.parsed_data
            token_type = TokenType(parsed_data.get("token", "SUI"))

            # Get balance
            balance_info = await sui_service.get_balance(
                address=request.user_address,
                token_type=token_type
            )

            # Convert amount to smallest units
            amount_str = parsed_data.get("amount", "0")
            decimals = 9  # SUI has 9 decimals
            amount_in_smallest = str(int(float(amount_str) * (10 ** decimals)))

            # Estimate gas
            estimated_gas = await sui_service.estimate_gas_fee(b"")

            # Generate dry-run summary
            dry_run = await openai_service.generate_dry_run_summary(
                action="stake_token",
                parsed_data={
                    "recipient": "Staking Pool",
                    "amount": amount_in_smallest,
                    "token": token_type.value
                },
                sender_balance=balance_info.balance,
                estimated_gas=estimated_gas
            )

            # Build transaction_data for execute endpoint
            transaction_data = {
                "action": "stake_token",
                "amount": amount_in_smallest,
                "token": token_type.value
            }
            logger.info(f"Stake transaction data prepared: {transaction_data}")

            return ChatResponse(
                intent=intent,
                dry_run=dry_run,
                ready_to_execute=True if dry_run.risk_level != "high" else False,
                message=f"Ready to stake {amount_str} {token_type.value}. Estimated gas: ~{dry_run.estimated_gas_fee} SUI.",
                transaction_data=transaction_data
            )

        elif intent.action == IntentAction.UNSTAKE_TOKEN:
            # Handle unstake
            logger.info("Handling UNSTAKE_TOKEN action")
            if not request.user_address:
                logger.warning("Unstake failed: no user address provided")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User address required for unstaking"
                )

            parsed_data = intent.parsed_data
            token_type = TokenType(parsed_data.get("token", "SUI"))

            # Get current stake
            stake_info = await sui_service.get_user_stake(
                user_address=request.user_address,
                token_type=token_type
            )

            # Get balance for gas estimation
            balance_info = await sui_service.get_balance(
                address=request.user_address,
                token_type=token_type
            )

            # Convert amount to smallest units
            amount_str = parsed_data.get("amount", "0")
            decimals = 9  # SUI has 9 decimals
            amount_in_smallest = str(int(float(amount_str) * (10 ** decimals)))

            # Check if user has enough staked
            if int(amount_in_smallest) > int(stake_info.staked_amount):
                logger.warning(f"Insufficient stake: requested {amount_in_smallest}, has {stake_info.staked_amount}")
                return ChatResponse(
                    intent=intent,
                    dry_run=None,
                    ready_to_execute=False,
                    message=f"Insufficient staked amount. You have {stake_info.staked_amount_formatted} {token_type.value} staked, but trying to unstake {amount_str} {token_type.value}."
                )

            # Estimate gas
            estimated_gas = await sui_service.estimate_gas_fee(b"")

            # Generate dry-run summary
            dry_run = await openai_service.generate_dry_run_summary(
                action="unstake_token",
                parsed_data={
                    "recipient": request.user_address,
                    "amount": amount_in_smallest,
                    "token": token_type.value
                },
                sender_balance=balance_info.balance,
                estimated_gas=estimated_gas
            )

            # Build transaction_data for execute endpoint
            transaction_data = {
                "action": "unstake_token",
                "amount": amount_in_smallest,
                "token": token_type.value
            }
            logger.info(f"Unstake transaction data prepared: {transaction_data}")

            return ChatResponse(
                intent=intent,
                dry_run=dry_run,
                ready_to_execute=True,
                message=f"Ready to unstake {amount_str} {token_type.value}. Estimated gas: ~{dry_run.estimated_gas_fee} SUI.",
                transaction_data=transaction_data
            )

        elif intent.action == IntentAction.TRANSFER_TOKEN:
            # Handle transfer
            logger.info("Handling TRANSFER_TOKEN action")
            if not request.user_address:
                logger.warning("Transfer failed: no user address provided")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User address required for transfers"
                )

            parsed_data = intent.parsed_data
            recipient = parsed_data.get("recipient")
            is_contact_name = parsed_data.get("is_contact_name", False)
            logger.info(f"Transfer details: recipient={recipient}, is_contact={is_contact_name}")

            # Step 2.1: Resolve contact if needed
            if is_contact_name:
                logger.info(f"Resolving contact name: {recipient}")
                
                # Check if user has an on-chain address book
                address_book = sui_service.get_user_address_book(request.user_address)
                if not address_book:
                    logger.warning(f"No address book found for user {request.user_address}")
                    return ChatResponse(
                        intent=intent,
                        dry_run=None,
                        ready_to_execute=False,
                        message=f"Contact '{recipient}' not found. You don't have an address book yet. Say 'Create my address book' to get started, then save contacts with 'Save [name] [address] as [key]'."
                    )

                # TODO: Read contacts from on-chain VecMap
                # For now, inform user that contact resolution from on-chain is coming
                # Users can still use direct wallet addresses
                logger.info(f"Address book found, but on-chain contact resolution is not yet implemented")
                return ChatResponse(
                    intent=intent,
                    dry_run=None,
                    ready_to_execute=False,
                    message=f"Contact name resolution is coming soon! For now, please use the full wallet address. You can check your saved contacts in Sui Explorer using your address book ID: {address_book['object_id'][:20]}..."
                )

            # Step 2.2: Get balance and generate dry-run
            token_type = TokenType(parsed_data.get("token", "SUI"))
            balance_info = await sui_service.get_balance(
                address=request.user_address,
                token_type=token_type
            )

            # Convert amount to smallest units (MIST for SUI, smallest for USDC)
            amount_str = parsed_data.get("amount", "0")
            decimals = 9 if token_type == TokenType.SUI else 6
            amount_in_smallest = str(int(float(amount_str) * (10 ** decimals)))

            # Estimate gas
            estimated_gas = await sui_service.estimate_gas_fee(b"")  # Simple estimation

            # Generate dry-run summary
            dry_run = await openai_service.generate_dry_run_summary(
                action="transfer_token",
                parsed_data={
                    "recipient": recipient,
                    "amount": amount_in_smallest,
                    "token": token_type.value
                },
                sender_balance=balance_info.balance,
                estimated_gas=estimated_gas
            )

            # Build transaction_data for execute endpoint
            transaction_data = {
                "action": "transfer_token",
                "recipient": recipient,
                "amount": amount_in_smallest,
                "token": token_type.value
            }
            logger.info(f"Transaction data prepared: {transaction_data}")

            return ChatResponse(
                intent=intent,
                dry_run=dry_run,
                ready_to_execute=True if dry_run.risk_level != "high" else False,
                message=f"Ready to {dry_run.action_description}. Estimated gas: ~{dry_run.estimated_gas_fee} SUI.",
                transaction_data=transaction_data
            )

        # =====================================================================
        # Address Book Operations
        # =====================================================================

        elif intent.action == IntentAction.CREATE_ADDRESS_BOOK:
            # Create on-chain address book
            logger.info("Handling CREATE_ADDRESS_BOOK action")
            if not request.user_address:
                logger.warning("Create address book failed: no user address provided")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User address required to create address book"
                )

            # Check if user already has an address book
            existing_book = sui_service.get_user_address_book(request.user_address)
            if existing_book:
                return ChatResponse(
                    intent=intent,
                    dry_run=None,
                    ready_to_execute=False,
                    message=f"You already have an address book (ID: {existing_book['object_id'][:16]}...). You can start saving contacts!"
                )

            # Build create address book transaction metadata
            tx_result = sui_service.build_create_address_book_tx(sender=request.user_address)

            transaction_data = {
                "action": "create_address_book",
                "transaction_type": tx_result.get("transaction_type"),
                "target": tx_result.get("target"),
                "arguments": tx_result.get("arguments", []),
                "type_arguments": tx_result.get("type_arguments", [])
            }

            return ChatResponse(
                intent=intent,
                dry_run=None,
                ready_to_execute=True,
                message="Ready to create your on-chain address book. This is a one-time setup that stores your contacts permanently on Sui. Estimated gas: ~0.01 SUI.",
                transaction_data=transaction_data
            )

        elif intent.action == IntentAction.SAVE_CONTACT:
            # Save contact to address book
            logger.info("Handling SAVE_CONTACT action")
            if not request.user_address:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User address required to save contact"
                )

            parsed_data = intent.parsed_data
            contact_key = parsed_data.get("contact_key", "").lower().replace(" ", "_")
            contact_name = parsed_data.get("contact_name", "")
            contact_address = parsed_data.get("contact_address", "")
            notes = parsed_data.get("notes", "")

            # Validate required fields
            if not contact_key or not contact_address:
                return ChatResponse(
                    intent=intent,
                    dry_run=None,
                    ready_to_execute=False,
                    message="I need a contact name/key and wallet address to save. Example: 'Save Alice's address 0x123... as alice'"
                )

            # Get user's address book
            address_book = sui_service.get_user_address_book(request.user_address)
            if not address_book:
                return ChatResponse(
                    intent=intent,
                    dry_run=None,
                    ready_to_execute=False,
                    message="You don't have an address book yet. Say 'Create my address book' first!"
                )

            # Encrypt contact data
            import time
            encrypted_data = await seal_service.encrypt_contact(
                user_address=request.user_address,
                name=contact_name,
                contact_address=contact_address,
                notes=notes
            )

            import os
            nonce = os.urandom(16)
            timestamp = int(time.time())

            # Build add contact transaction metadata
            tx_result = sui_service.build_add_contact_tx(
                sender=request.user_address,
                address_book_id=address_book["object_id"],
                contact_key=contact_key,
                encrypted_data=encrypted_data,
                nonce=nonce,
                timestamp=timestamp
            )

            transaction_data = {
                "action": "save_contact",
                "transaction_type": tx_result.get("transaction_type"),
                "target": tx_result.get("target"),
                "arguments": tx_result.get("arguments", []),
                "type_arguments": tx_result.get("type_arguments", []),
                "contact_key": contact_key,
                "contact_name": contact_name
            }

            return ChatResponse(
                intent=intent,
                dry_run=None,
                ready_to_execute=True,
                message=f"Ready to save '{contact_name}' as '{contact_key}' to your address book. This will be encrypted and stored on-chain. Estimated gas: ~0.02 SUI.",
                transaction_data=transaction_data
            )

        elif intent.action == IntentAction.LIST_CONTACTS:
            # List all contacts
            logger.info("Handling LIST_CONTACTS action")
            if not request.user_address:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User address required to list contacts"
                )

            # Get user's address book
            address_book = sui_service.get_user_address_book(request.user_address)
            if not address_book:
                return ChatResponse(
                    intent=intent,
                    dry_run=None,
                    ready_to_execute=False,
                    message="You don't have an address book yet. Say 'Create my address book' to get started!"
                )

            # For now, we just confirm the address book exists
            # Full contact listing would require reading the VecMap from on-chain
            return ChatResponse(
                intent=intent,
                dry_run=None,
                ready_to_execute=False,
                message=f"Your address book (ID: {address_book['object_id'][:16]}...) is ready. Contact listing from on-chain data is coming soon! For now, you can save contacts using 'Save [name] [address] as [key]'."
            )

        else:
            # Unknown action
            return ChatResponse(
                intent=intent,
                dry_run=None,
                ready_to_execute=False,
                message="I didn't understand that. Could you rephrase?"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )


@router.post("/execute", response_model=TransactionResult)
async def execute_transaction(request: ExecuteTransactionRequest):
    """
    Execute a blockchain transaction (REAL EXECUTION!)

    This endpoint builds, signs, and executes the transaction on Sui blockchain.

    Args:
        request: Transaction data from /chat endpoint, including optional private_key

    Returns:
        TransactionResult with real digest on success
        
    Raises:
        HTTPException 400: For validation errors or missing required fields
        HTTPException 500: For transaction execution failures

    Security Note: In production, signing should happen client-side.
    Private keys should NEVER be sent to the backend.
    """
    logger.info(f"=== Execute Transaction Request ===")
    logger.info(f"User Address: {request.user_address}")
    logger.debug(f"Transaction Data: {request.transaction_data}")
    
    try:
        # Extract transaction details
        tx_data = request.transaction_data
        action = tx_data.get("action")
        private_key = tx_data.get("private_key")  # Now from request body

        logger.info(f"Action: {action}")
        logger.info(f"Private key provided: {'Yes' if private_key else 'No'}")

        if action == "stake_token":
            amount = tx_data.get("amount")
            token = tx_data.get("token", "SUI")

            logger.info(f"Stake: {amount} {token}")

            # Validate required fields
            if not amount:
                logger.error("Missing amount in transaction data")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing amount in transaction data"
                )

            # If private key provided, use WalletService
            if private_key:
                logger.info("Private key provided, using WalletService to build and execute stake...")
                from services.wallet_service import WalletService

                try:
                    wallet = WalletService(private_key)

                    # Build stake transaction
                    logger.info("Building stake transaction...")
                    tx_data_dict = await sui_service.build_stake_transaction(
                        sender=wallet.get_address(),
                        amount=amount,
                        token_type=TokenType(token)
                    )

                    # Execute with wallet
                    logger.info("Executing stake transaction...")
                    result = await wallet.execute_transaction(tx_data_dict["transaction_bytes"])

                    if result.success:
                        logger.info(f"Stake SUCCESS! Digest: {result.transaction_digest}")
                        return result
                    else:
                        logger.error(f"Stake FAILED: {result.error}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Stake execution failed: {result.error}"
                        )
                except ValueError as e:
                    logger.error(f"Wallet error: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Wallet error: {str(e)}"
                    )
            else:
                # No private key - build for client-side signing
                logger.info("No private key. Building stake transaction for client-side signing...")
                try:
                    tx_bytes_dict = await sui_service.build_stake_transaction(
                        sender=request.user_address,
                        amount=amount,
                        token_type=TokenType(token)
                    )
                    tx_hex = tx_bytes_dict["transaction_bytes"].hex()
                    logger.info("Stake transaction built successfully")

                    return TransactionResult(
                        success=True,
                        effects={
                            "status": "ready_for_signing",
                            "transaction_bytes": tx_hex,
                            "message": "Stake transaction built. Sign with your wallet to execute."
                        }
                    )
                except ValueError as e:
                    logger.error(f"Failed to build stake transaction: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to build stake transaction: {str(e)}"
                    )

        elif action == "unstake_token":
            amount = tx_data.get("amount")
            token = tx_data.get("token", "SUI")

            logger.info(f"Unstake: {amount} {token}")

            # Validate required fields
            if not amount:
                logger.error("Missing amount in transaction data")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing amount in transaction data"
                )

            # If private key provided, use WalletService
            if private_key:
                logger.info("Private key provided, using WalletService to build and execute unstake...")
                from services.wallet_service import WalletService

                try:
                    wallet = WalletService(private_key)

                    # Build unstake transaction
                    logger.info("Building unstake transaction...")
                    tx_data_dict = await sui_service.build_unstake_transaction(
                        sender=wallet.get_address(),
                        amount=amount,
                        token_type=TokenType(token)
                    )

                    # Execute with wallet
                    logger.info("Executing unstake transaction...")
                    result = await wallet.execute_transaction(tx_data_dict["transaction_bytes"])

                    if result.success:
                        logger.info(f"Unstake SUCCESS! Digest: {result.transaction_digest}")
                        return result
                    else:
                        logger.error(f"Unstake FAILED: {result.error}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Unstake execution failed: {result.error}"
                        )
                except ValueError as e:
                    logger.error(f"Wallet error: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Wallet error: {str(e)}"
                    )
            else:
                # No private key - build for client-side signing
                logger.info("No private key. Building unstake transaction for client-side signing...")
                try:
                    tx_bytes_dict = await sui_service.build_unstake_transaction(
                        sender=request.user_address,
                        amount=amount,
                        token_type=TokenType(token)
                    )
                    tx_hex = tx_bytes_dict["transaction_bytes"].hex()
                    logger.info("Unstake transaction built successfully")

                    return TransactionResult(
                        success=True,
                        effects={
                            "status": "ready_for_signing",
                            "transaction_bytes": tx_hex,
                            "message": "Unstake transaction built. Sign with your wallet to execute."
                        }
                    )
                except ValueError as e:
                    logger.error(f"Failed to build unstake transaction: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to build unstake transaction: {str(e)}"
                    )

        elif action == "transfer_token":
            recipient = tx_data.get("recipient")
            amount = tx_data.get("amount")
            token = tx_data.get("token", "SUI")
            
            logger.info(f"Transfer: {amount} {token} to {recipient}")
            
            # Validate required fields
            if not recipient:
                logger.error("Missing recipient in transaction data")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing recipient address in transaction data"
                )
            
            if not amount:
                logger.error("Missing amount in transaction data")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing amount in transaction data"
                )
            
            # If private key provided, use WalletService to build AND execute
            if private_key:
                logger.info("Private key provided, using WalletService to build and execute...")
                from services.wallet_service import WalletService

                try:
                    # Initialize wallet with private key
                    logger.debug("Initializing wallet with private key...")
                    wallet = WalletService(private_key)

                    # Build and execute transaction using wallet's config (with imported keypair)
                    logger.info("Building and executing transaction on Sui blockchain...")
                    result = await wallet.build_and_execute_transfer(
                        recipient=recipient,
                        amount=amount,
                        token_type=TokenType(token)
                    )
                    
                    if result.success:
                        logger.info(f"Transaction SUCCESS! Digest: {result.transaction_digest}")
                        return result
                    else:
                        logger.error(f"Transaction FAILED: {result.error}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Transaction execution failed: {result.error}"
                        )
                except ValueError as e:
                    logger.error(f"Wallet error: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Wallet error: {str(e)}"
                    )

            else:
                # No private key - build transaction for client-side signing
                logger.info("No private key provided. Building transaction for client-side signing...")
                try:
                    tx_bytes_dict = await sui_service.build_transfer_transaction(
                        sender=request.user_address,
                        recipient=recipient,
                        amount=amount,
                        token_type=TokenType(token)
                    )
                    tx_hex = tx_bytes_dict["transaction_bytes"].hex()
                    logger.info("Transaction built successfully for client-side signing")
                    logger.debug(f"Transaction bytes (hex): {tx_hex[:100]}...")
                    
                    return TransactionResult(
                        success=True,  # Transaction was built successfully
                        effects={
                            "status": "ready_for_signing",
                            "transaction_bytes": tx_hex,
                            "message": "Transaction built successfully. Sign with your wallet to execute."
                        }
                    )
                except ValueError as e:
                    logger.error(f"Failed to build transaction: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to build transaction: {str(e)}"
                    )

        else:
            logger.error(f"Unsupported action: {action}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported action: {action}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execute transaction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/contacts/save", response_model=Dict[str, str])
async def save_contact(request: ContactRequest):
    """
    Save encrypted contact to Walrus

    Privacy Flow:
    1. Encrypt contact data with user's signature
    2. Upload encrypted blob to Walrus
    3. Store blob_id mapped to user address

    Args:
        request: Contact details to save

    Returns:
        Success message with blob_id
    """
    try:
        if not request.contact_name or not request.contact_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact name and address are required"
            )

        # Check if user already has contacts
        if request.user_address in contact_storage:
            # Download existing contacts
            blob_id = contact_storage[request.user_address]
            encrypted_data = await walrus_service.download_blob(blob_id)
            existing_contacts = await seal_service.decrypt_bulk_contacts(
                user_address=request.user_address,
                encrypted_data=encrypted_data
            )

            # Add new contact
            existing_contacts.append({
                "name": request.contact_name,
                "address": request.contact_address,
                "notes": request.notes
            })

            # Re-encrypt and upload
            encrypted_blob = await seal_service.encrypt_bulk_contacts(
                user_address=request.user_address,
                contacts=[c.model_dump() if isinstance(c, ContactInfo) else c for c in existing_contacts]
            )
        else:
            # First contact - encrypt single contact
            encrypted_blob = await seal_service.encrypt_bulk_contacts(
                user_address=request.user_address,
                contacts=[{
                    "name": request.contact_name,
                    "address": request.contact_address,
                    "notes": request.notes
                }]
            )

        # Upload to Walrus
        upload_result = await walrus_service.upload_blob(encrypted_blob)

        # Store blob_id
        contact_storage[request.user_address] = upload_result.blob_id

        return {
            "message": "Contact saved successfully",
            "blob_id": upload_result.blob_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving contact: {str(e)}"
        )


@router.get("/contacts/list")
async def list_contacts(user_address: str):
    """
    List all contacts for a user (decrypted)

    Args:
        user_address: User's wallet address

    Returns:
        List of decrypted contacts
    """
    try:
        if user_address not in contact_storage:
            return {"contacts": []}

        # Download and decrypt contacts
        blob_id = contact_storage[user_address]
        encrypted_data = await walrus_service.download_blob(blob_id)
        contacts = await seal_service.decrypt_bulk_contacts(
            user_address=user_address,
            encrypted_data=encrypted_data
        )

        return {"contacts": [c.model_dump() for c in contacts]}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving contacts: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Sui Blockchain AI Agent",
        "version": "1.0.0-mvp"
    }
