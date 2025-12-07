"""
Walrus Storage Service - Decentralized Storage for Encrypted Contacts

Walrus is a decentralized blob storage system on Sui blockchain.
We use it to store ENCRYPTED contact data with high availability and low cost.

PRIVACY-FIRST ARCHITECTURE:
1. Contact data is encrypted BEFORE uploading to Walrus (using Seal Service)
2. Walrus stores only encrypted blobs - no plaintext names/addresses
3. Blob IDs are stored on-chain or in local DB
4. Only users with correct signatures can decrypt after retrieval

WHY WALRUS?
- Decentralized: No single point of failure
- Cost-effective: ~20x cheaper than on-chain storage
- Permanent: Data persists for specified epochs
- Privacy-compatible: Perfect for encrypted data storage
"""

import httpx
import json
import logging
from typing import Optional

# Configure logger for this module
logger = logging.getLogger(__name__)
from config import settings
from models.schemas import WalrusUploadResponse


class WalrusService:
    """
    Walrus Storage Service for encrypted contact management

    Handles upload/download of encrypted blobs to/from Walrus network.
    All data is encrypted before upload to ensure privacy.
    """

    def __init__(self):
        self.publisher_url = settings.WALRUS_PUBLISHER_URL
        self.aggregator_url = settings.WALRUS_AGGREGATOR_URL
        self.default_epochs = 5  # Storage duration in epochs (~2 weeks per epoch)

    async def upload_blob(
        self,
        data: bytes,
        epochs: int = None
    ) -> WalrusUploadResponse:
        """
        Upload encrypted data blob to Walrus

        PRIVACY NOTE:
        - 'data' should ALWAYS be encrypted before calling this method
        - Walrus stores public blobs, encryption is our privacy layer

        Args:
            data: Encrypted bytes (from Seal Service)
            epochs: Number of epochs to store (default: 5)

        Returns:
            WalrusUploadResponse with blob_id

        Raises:
            httpx.HTTPError: If upload fails
        """
        epochs = epochs or self.default_epochs

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Walrus Publisher API endpoint for storing blobs
            url = f"{self.publisher_url}/v1/blobs"

            # Upload parameters
            params = {
                "epochs": epochs
            }

            # Upload the blob
            response = await client.put(
                url,
                params=params,
                content=data,
                headers={
                    "Content-Type": "application/octet-stream"
                }
            )

            response.raise_for_status()

            # Parse response
            result = response.json()

            # Walrus returns different formats, handle both
            if "newlyCreated" in result:
                blob_info = result["newlyCreated"]["blobObject"]
                blob_id = blob_info["blobId"]
                size = blob_info["size"]
            elif "alreadyCertified" in result:
                blob_info = result["alreadyCertified"]["blobObject"]
                blob_id = blob_info["blobId"]
                size = blob_info["size"]
            else:
                raise ValueError(f"Unexpected Walrus response format: {result}")

            return WalrusUploadResponse(
                blob_id=blob_id,
                size=int(size),
                epochs=epochs
            )

    async def download_blob(self, blob_id: str) -> bytes:
        """
        Download encrypted blob from Walrus

        PRIVACY NOTE:
        - Returns encrypted bytes
        - Must be decrypted using Seal Service with correct user signature

        Args:
            blob_id: Blob ID from previous upload

        Returns:
            Encrypted bytes

        Raises:
            httpx.HTTPError: If download fails
            ValueError: If blob not found
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Walrus Aggregator API endpoint for reading blobs
            url = f"{self.aggregator_url}/v1/{blob_id}"

            response = await client.get(url)

            if response.status_code == 404:
                raise ValueError(f"Blob not found: {blob_id}")

            response.raise_for_status()

            return response.content

    async def check_blob_availability(self, blob_id: str) -> bool:
        """
        Check if a blob exists and is available on Walrus

        Args:
            blob_id: Blob ID to check

        Returns:
            True if blob exists and is accessible
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.aggregator_url}/v1/{blob_id}"
                response = await client.head(url)
                return response.status_code == 200
        except Exception:
            return False

    async def get_blob_metadata(self, blob_id: str) -> dict:
        """
        Get metadata about a stored blob (size, availability, etc.)

        NOTE: This is a helper method for debugging/monitoring.
        Walrus doesn't provide extensive metadata via HTTP API.

        Args:
            blob_id: Blob ID

        Returns:
            Dictionary with available metadata
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.aggregator_url}/v1/{blob_id}"
                response = await client.head(url)

                if response.status_code == 200:
                    return {
                        "blob_id": blob_id,
                        "available": True,
                        "size": response.headers.get("content-length"),
                        "content_type": response.headers.get("content-type")
                    }
                else:
                    return {
                        "blob_id": blob_id,
                        "available": False
                    }
        except Exception as e:
            return {
                "blob_id": blob_id,
                "available": False,
                "error": str(e)
            }


# Global service instance
walrus_service = WalrusService()
