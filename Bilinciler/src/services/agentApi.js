/**
 * Blockchain AI Agent API Service
 * Connects frontend with the Python backend at localhost:8000
 */

// Use proxy in development (/backend routes to localhost:8000 via vite.config.ts)
const API_BASE_URL = import.meta.env.DEV
    ? '/backend/api/v1'
    : (import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000/api/v1');

// Contacts API uses a different base URL (no /api/v1 prefix)
const CONTACTS_BASE_URL = import.meta.env.DEV
    ? '/backend/contacts'
    : (import.meta.env.VITE_BACKEND_URL?.replace('/api/v1', '/contacts') || 'http://localhost:8000/contacts');

/**
 * Send a chat message to the AI agent
 * @param {string} message - Natural language message
 * @param {string} userAddress - User's wallet address
 * @returns {Promise<Object>} - Agent response with intent and dry-run
 */
export async function sendChatMessage(message, userAddress) {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                user_address: userAddress,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to process message');
        }

        return data;
    } catch (error) {
        console.error('Chat API Error:', error);
        throw error;
    }
}

/**
 * Execute a prepared transaction
 * @param {Object} transactionData - Transaction data from chat response
 * @param {string} userAddress - User's wallet address
 * @param {string} privateKey - Optional private key for signing
 * @returns {Promise<Object>} - Transaction result
 */
export async function executeTransaction(transactionData, userAddress, privateKey = null) {
    try {
        const response = await fetch(`${API_BASE_URL}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_address: userAddress,
                transaction_data: transactionData,
                private_key: privateKey,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Transaction failed');
        }

        return data;
    } catch (error) {
        console.error('Execute API Error:', error);
        throw error;
    }
}

/**
 * Get wallet balance
 * @param {string} userAddress - Wallet address
 * @param {string} token - Token type (SUI, USDC)
 * @returns {Promise<Object>} - Balance info
 */
export async function getBalance(userAddress, token = 'SUI') {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: `What is my ${token} balance?`,
                user_address: userAddress,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to get balance');
        }

        return data;
    } catch (error) {
        console.error('Balance API Error:', error);
        throw error;
    }
}

// ============================================================================
// On-Chain Contact Storage (AddressBook)
// ============================================================================

/**
 * Create a new on-chain address book for the user
 * Returns transaction bytes that need to be signed by user's wallet
 * @param {string} userAddress - User's wallet address
 * @returns {Promise<Object>} - Transaction bytes for signing
 */
export async function createAddressBook(userAddress) {
    try {
        const response = await fetch(`${CONTACTS_BASE_URL}/address-book/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sender_address: userAddress,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to create address book');
        }

        return data;
    } catch (error) {
        console.error('Create AddressBook Error:', error);
        throw error;
    }
}

/**
 * Check if user has an existing address book
 * @param {string} userAddress - User's wallet address
 * @returns {Promise<Object>} - Address book info { exists, object_id, owner }
 */
export async function getAddressBookInfo(userAddress) {
    try {
        const response = await fetch(`${CONTACTS_BASE_URL}/address-book/info`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_address: userAddress,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to get address book info');
        }

        return data;
    } catch (error) {
        console.error('Get AddressBook Info Error:', error);
        throw error;
    }
}

/**
 * Add a contact to user's on-chain address book
 * Returns transaction bytes that need to be signed by user's wallet
 * @param {string} userAddress - User's wallet address
 * @param {string} addressBookId - User's AddressBook object ID
 * @param {string} contactKey - Simple key for the contact (e.g., "alice", "mom")
 * @param {string} contactName - Contact display name
 * @param {string} contactAddress - Contact's wallet address
 * @param {string} notes - Optional notes
 * @returns {Promise<Object>} - Transaction bytes for signing
 */
export async function addContact(userAddress, addressBookId, contactKey, contactName, contactAddress, notes = '') {
    try {
        const response = await fetch(`${CONTACTS_BASE_URL}/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sender_address: userAddress,
                address_book_id: addressBookId,
                contact_key: contactKey,
                contact_name: contactName,
                contact_address: contactAddress,
                notes,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to add contact');
        }

        return data;
    } catch (error) {
        console.error('Add Contact Error:', error);
        throw error;
    }
}

/**
 * @deprecated Use addContact with on-chain storage instead
 * Save a contact (legacy Walrus-based endpoint)
 */
export async function saveContact(userAddress, contactName, contactAddress, notes = '') {
    console.warn('saveContact is deprecated. Use addContact with on-chain storage instead.');
    throw new Error('This endpoint has been deprecated. Please use createAddressBook and addContact for on-chain storage.');
}

/**
 * @deprecated Use on-chain storage instead
 * List all contacts for a user (legacy Walrus-based endpoint)
 */
export async function listContacts(userAddress) {
    console.warn('listContacts is deprecated. Contacts are now stored on-chain.');
    throw new Error('This endpoint has been deprecated. Contacts are now stored on-chain in your AddressBook.');
}

/**
 * Contact health check
 * @returns {Promise<Object>} - Health status
 */
export async function contactsHealthCheck() {
    try {
        const response = await fetch(`${CONTACTS_BASE_URL}/health`);
        return await response.json();
    } catch (error) {
        console.error('Contacts Health Check Error:', error);
        return { status: 'unhealthy', error: error.message };
    }
}

/**
 * Health check
 * @returns {Promise<Object>} - Health status
 */
export async function healthCheck() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        return await response.json();
    } catch (error) {
        console.error('Health Check Error:', error);
        return { status: 'unhealthy', error: error.message };
    }
}

export default {
    sendChatMessage,
    executeTransaction,
    getBalance,
    // On-chain contacts
    createAddressBook,
    getAddressBookInfo,
    addContact,
    contactsHealthCheck,
    // Legacy (deprecated)
    saveContact,
    listContacts,
    healthCheck,
};

