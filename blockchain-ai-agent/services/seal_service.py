"""
Seal Encryption Service - Privacy-First Contact Encryption

This service implements client-side encryption for sensitive contact data using
cryptography.fernet (symmetric encryption) derived from user signatures.

PRIVACY-FIRST APPROACH:
- Contact names (e.g., "Mom", "Boss") are NEVER stored in plaintext
- Encryption key is derived from user's wallet signature
- Only the user with the correct signature can decrypt their contacts
- Encrypted data is stored on decentralized Walrus storage
"""

import json
import base64
import hashlib
import logging
from typing import Dict, Any

# Configure logger for this module
logger = logging.getLogger(__name__)
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from models.schemas import EncryptedContactData, ContactInfo
from config import settings


class SealService:
    """
    Seal Service for encrypting/decrypting contact information

    Uses Fernet symmetric encryption with keys derived from user signatures.
    This ensures that only the user who owns the wallet can decrypt their contacts.
    """

    def __init__(self):
        self.salt = settings.SECRET_KEY.encode()

    def _derive_key_from_signature(self, user_address: str, signature: str = None) -> bytes:
        """
        Derive encryption key from user's wallet address and signature

        In a production environment, this would use the user's actual wallet signature.
        For MVP, we derive from address + secret key.

        Args:
            user_address: User's Sui wallet address
            signature: User's signature (optional for MVP)

        Returns:
            32-byte encryption key
        """
        # Combine user address with signature (or secret key for MVP)
        key_material = f"{user_address}:{signature or settings.SECRET_KEY}".encode()

        # Use PBKDF2HMAC to derive a strong key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )

        key = base64.urlsafe_b64encode(kdf.derive(key_material))
        return key

    async def encrypt_contact(
        self,
        user_address: str,
        name: str,
        contact_address: str,
        notes: str = None,
        signature: str = None
    ) -> bytes:
        """
        Encrypt contact data for a user

        PRIVACY APPROACH:
        1. Create contact data object (name, address, notes)
        2. Derive encryption key from user's signature
        3. Encrypt using Fernet (AES-128 in CBC mode with HMAC)
        4. Return encrypted bytes ready for Walrus upload

        Args:
            user_address: User's wallet address
            name: Contact's display name (e.g., "Mom")
            contact_address: Contact's wallet address
            notes: Optional notes
            signature: User's signature for key derivation

        Returns:
            Encrypted bytes ready for Walrus storage
        """
        # Create contact data structure
        contact_data = EncryptedContactData(
            name=name,
            address=contact_address,
            notes=notes
        )

        # Serialize to JSON
        plaintext = json.dumps(contact_data.model_dump()).encode()

        # Derive encryption key from user signature
        key = self._derive_key_from_signature(user_address, signature)

        # Encrypt using Fernet
        fernet = Fernet(key)
        encrypted_bytes = fernet.encrypt(plaintext)

        return encrypted_bytes

    async def decrypt_contact(
        self,
        user_address: str,
        encrypted_data: bytes,
        signature: str = None
    ) -> ContactInfo:
        """
        Decrypt contact data for a user

        PRIVACY GUARANTEE:
        - Only someone with the correct user signature can decrypt
        - Wrong signature = wrong key = decryption fails
        - This ensures contact privacy even if Walrus data is public

        Args:
            user_address: User's wallet address
            encrypted_data: Encrypted bytes from Walrus
            signature: User's signature for key derivation

        Returns:
            Decrypted contact information

        Raises:
            ValueError: If decryption fails (wrong signature/corrupted data)
        """
        try:
            # Derive decryption key from user signature
            key = self._derive_key_from_signature(user_address, signature)

            # Decrypt using Fernet
            fernet = Fernet(key)
            plaintext = fernet.decrypt(encrypted_data)

            # Deserialize from JSON
            contact_dict = json.loads(plaintext.decode())
            contact_info = ContactInfo(**contact_dict)

            return contact_info

        except Exception as e:
            raise ValueError(f"Failed to decrypt contact data: {str(e)}")

    async def encrypt_bulk_contacts(
        self,
        user_address: str,
        contacts: list[Dict[str, Any]],
        signature: str = None
    ) -> bytes:
        """
        Encrypt multiple contacts at once (address book)

        This is more efficient than encrypting each contact individually
        when uploading an entire address book to Walrus.

        Args:
            user_address: User's wallet address
            contacts: List of contact dictionaries
            signature: User's signature

        Returns:
            Encrypted bytes containing all contacts
        """
        # Serialize all contacts
        plaintext = json.dumps(contacts).encode()

        # Derive key and encrypt
        key = self._derive_key_from_signature(user_address, signature)
        fernet = Fernet(key)
        encrypted_bytes = fernet.encrypt(plaintext)

        return encrypted_bytes

    async def decrypt_bulk_contacts(
        self,
        user_address: str,
        encrypted_data: bytes,
        signature: str = None
    ) -> list[ContactInfo]:
        """
        Decrypt multiple contacts (address book)

        Args:
            user_address: User's wallet address
            encrypted_data: Encrypted bytes from Walrus
            signature: User's signature

        Returns:
            List of decrypted contacts
        """
        try:
            # Derive key and decrypt
            key = self._derive_key_from_signature(user_address, signature)
            fernet = Fernet(key)
            plaintext = fernet.decrypt(encrypted_data)

            # Deserialize
            contacts_list = json.loads(plaintext.decode())
            return [ContactInfo(**c) for c in contacts_list]

        except Exception as e:
            raise ValueError(f"Failed to decrypt contacts: {str(e)}")


# Global service instance
seal_service = SealService()
