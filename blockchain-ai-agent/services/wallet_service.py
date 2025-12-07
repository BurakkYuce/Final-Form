"""
Wallet Service - Real Transaction Signing & Execution

Handles wallet operations including:
- Importing wallets from private keys
- Signing transactions
- Executing transactions on Sui blockchain
"""

import logging
from typing import Optional, Dict, Any

# Configure logger for this module
logger = logging.getLogger(__name__)
from pysui import SuiConfig, SyncClient
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_crypto import SuiPrivateKey
from pysui.sui.sui_txn import SyncTransaction

from config import settings
from models.schemas import TransactionResult, TokenType


class WalletService:
    """
    Wallet Service for signing and executing real blockchain transactions

    SECURITY WARNING: In production, private keys should NEVER be stored in code.
    This is for testing purposes only.
    """

    def __init__(self, private_key_str: str = None):
        """
        Initialize wallet service

        Args:
            private_key_str: Sui private key in format 'suiprivkey1q...'
        """
        logger.info("Initializing WalletService...")
        # Initialize Sui client
        self.config = SuiConfig.user_config(
            rpc_url=settings.SUI_RPC_URL
        )
        self.client = SyncClient(self.config)

        # Import private key if provided
        self.private_key = None
        self.address = None
        if private_key_str:
            self.address = self.import_private_key(private_key_str)
            logger.info(f"Wallet initialized with address: {self.address}")

    def import_private_key(self, private_key_str: str) -> SuiAddress:
        """
        Import a wallet from private key

        Args:
            private_key_str: Private key string (suiprivkey1q...)

        Returns:
            Wallet address
        """
        try:
            logger.debug("Importing private key...")
            # Add keypair to config from keystring (returns address directly)
            address = self.config.add_keypair_from_keystring(
                keystring=private_key_str,
                install=True,
                make_active=True
            )

            # Get the keypair from config
            self.private_key = self.config.keypair_for_address(address)
            logger.info(f"Private key imported successfully for address: {address}")

            return address

        except Exception as e:
            logger.error(f"Failed to import private key: {str(e)}")
            raise ValueError(f"Failed to import private key: {str(e)}")

    async def build_and_execute_transfer(
        self,
        recipient: str,
        amount: str,
        token_type: TokenType = TokenType.SUI
    ) -> TransactionResult:
        """
        Build AND execute a transfer transaction using the imported wallet.
        
        This method builds the transaction using the config with imported keypair,
        which solves the 'address not found' issue.

        Args:
            recipient: Recipient's wallet address
            amount: Amount in smallest units (MIST for SUI)
            token_type: Type of token to transfer

        Returns:
            TransactionResult with real transaction digest and effects
        """
        logger.info(f"Building and executing transfer: {amount} {token_type.value} to {recipient}")
        
        try:
            if not self.private_key or not self.address:
                raise ValueError("No private key imported. Import a private key first.")

            recipient_address = SuiAddress(recipient)
            amount_int = int(amount)
            
            logger.debug(f"Sender: {self.address}")
            logger.debug(f"Recipient: {recipient_address}")
            logger.debug(f"Amount: {amount_int} {token_type.value}")

            # Create transaction using config with imported keypair
            logger.info("Creating transaction builder...")
            txn = SyncTransaction(
                client=self.client,
                initial_sender=self.address
            )

            if token_type == TokenType.SUI:
                # Split coins for exact amount transfer
                logger.debug("Splitting SUI coins for transfer...")
                split_coin = txn.split_coin(
                    coin=txn.gas,
                    amounts=[amount_int]
                )

                # Transfer the split coin to recipient
                logger.debug("Adding transfer command...")
                txn.transfer_objects(
                    transfers=[split_coin],
                    recipient=recipient_address
                )
            else:
                raise ValueError(f"Token type {token_type} not yet implemented")

            # Execute the transaction
            logger.info("Executing transaction on blockchain...")
            result = txn.execute(gas_budget=10000000)  # 0.01 SUI max gas

            if result.is_ok():
                tx_data = result.result_data
                logger.info(f"Transaction SUCCESS! Digest: {tx_data.digest}")
                
                return TransactionResult(
                    success=True,
                    transaction_digest=tx_data.digest,
                    effects={
                        "status": tx_data.effects.status.status if tx_data.effects else "unknown",
                        "gas_used": str(tx_data.effects.gas_used.computation_cost) if tx_data.effects else "0"
                    }
                )
            else:
                error_msg = result.result_string
                logger.error(f"Transaction FAILED: {error_msg}")
                return TransactionResult(
                    success=False,
                    error=f"Transaction failed: {error_msg}"
                )

        except Exception as e:
            logger.error(f"Error in build_and_execute_transfer: {str(e)}", exc_info=True)
            return TransactionResult(
                success=False,
                error=f"Transaction error: {str(e)}"
            )


    async def sign_and_execute_transaction(
        self,
        transaction_bytes: bytes,
        sender_address: str
    ) -> TransactionResult:
        """
        Sign and execute a transaction on Sui blockchain

        This is the REAL transaction execution (not simulated!)

        Args:
            transaction_bytes: Built transaction bytes from SuiService
            sender_address: Sender's address for verification

        Returns:
            TransactionResult with real transaction digest and effects
        """
        try:
            if not self.private_key:
                raise ValueError("No private key imported. Call import_private_key first.")

            # Verify sender address matches wallet
            if str(self.address) != sender_address:
                raise ValueError(
                    f"Sender address mismatch. "
                    f"Wallet: {str(self.address)}, Sender: {sender_address}"
                )

            # Sign transaction
            signature = self.private_key.new_sign_secure(transaction_bytes)

            # Execute on blockchain
            result = self.client.execute_transaction_block(
                tx_bytes=transaction_bytes,
                signatures=[signature]
            )

            if result.is_ok():
                tx_data = result.result_data

                return TransactionResult(
                    success=True,
                    transaction_digest=tx_data.digest,
                    effects={
                        "status": tx_data.effects.status.status,
                        "gas_used": str(tx_data.effects.gas_used.computation_cost),
                        "events": len(tx_data.effects.events) if tx_data.effects.events else 0
                    }
                )
            else:
                return TransactionResult(
                    success=False,
                    error=f"Transaction failed: {result.result_string}"
                )

        except Exception as e:
            return TransactionResult(
                success=False,
                error=f"Transaction execution error: {str(e)}"
            )

    def get_balance(self, address: str = None) -> Dict[str, Any]:
        """
        Get balance for an address

        Args:
            address: Address to check (defaults to wallet address)

        Returns:
            Balance information
        """
        try:
            if address is None:
                if not self.address:
                    raise ValueError("No address provided and no wallet loaded")
                address = str(self.address)  # Convert SuiString to string

            sui_address = SuiAddress(address)
            result = self.client.get_gas(sui_address)

            if result.is_ok():
                total_balance = sum(int(coin.balance) for coin in result.result_data.data)
                return {
                    "address": address,
                    "balance_mist": total_balance,
                    "balance_sui": total_balance / 1_000_000_000,
                    "coin_count": len(result.result_data.data)
                }
            else:
                raise ValueError(f"Failed to get balance: {result.result_string}")

        except Exception as e:
            raise ValueError(f"Error getting balance: {str(e)}")


# Global wallet instance (for testing)
# In production, this should be managed per-user with secure key storage
wallet_service = None


def initialize_wallet(private_key: str) -> WalletService:
    """
    Initialize global wallet service

    Args:
        private_key: Private key string

    Returns:
        Initialized WalletService
    """
    global wallet_service
    wallet_service = WalletService(private_key)
    return wallet_service
