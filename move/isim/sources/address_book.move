/// On-Chain Address Book with Seal Encryption Support
/// 
/// This module provides permanent on-chain storage for encrypted contacts.
/// Contact data is encrypted client-side using Seal before storing.
/// 
/// Storage Cost: ~76 MIST per byte (one-time payment, permanent storage)
/// Delete Rebate: 99% refund when contact is removed

module isim::address_book {
    use sui::vec_map::{Self, VecMap};
    use sui::event;
    use std::string::String;

    // ============================================================================
    // Error Codes
    // ============================================================================
    
    const EContactNotFound: u64 = 0;
    const EContactAlreadyExists: u64 = 1;
    const EEmptyName: u64 = 2;

    // ============================================================================
    // Structs
    // ============================================================================

    /// Encrypted contact data stored on-chain
    /// The actual name, address, and notes are encrypted client-side
    public struct EncryptedContact has store, drop, copy {
        /// Seal-encrypted contact data (contains: name, address, notes)
        encrypted_data: vector<u8>,
        /// Encryption nonce/IV for decryption
        nonce: vector<u8>,
        /// Timestamp when contact was added
        created_at: u64,
        /// Timestamp of last update
        updated_at: u64,
    }

    /// User's address book - owned object attached to user's wallet
    public struct AddressBook has key, store {
        id: UID,
        /// Owner's address (for reference)
        owner: address,
        /// Map of contact key (plaintext) -> encrypted contact data
        /// Key can be a simple identifier like "alice", "mom", "exchange1"
        contacts: VecMap<String, EncryptedContact>,
        /// Total number of contacts
        contact_count: u64,
    }

    // ============================================================================
    // Events
    // ============================================================================

    /// Emitted when a new address book is created
    public struct AddressBookCreated has copy, drop {
        book_id: address,
        owner: address,
    }

    /// Emitted when a contact is added
    public struct ContactAdded has copy, drop {
        book_id: address,
        contact_key: String,
    }

    /// Emitted when a contact is updated
    public struct ContactUpdated has copy, drop {
        book_id: address,
        contact_key: String,
    }

    /// Emitted when a contact is removed
    public struct ContactRemoved has copy, drop {
        book_id: address,
        contact_key: String,
    }

    // ============================================================================
    // Public Functions
    // ============================================================================

    /// Create a new address book for the caller
    /// The address book is transferred to the caller's address
    public fun create_address_book(ctx: &mut TxContext) {
        let sender = ctx.sender();
        
        let book = AddressBook {
            id: object::new(ctx),
            owner: sender,
            contacts: vec_map::empty(),
            contact_count: 0,
        };

        let book_id = object::uid_to_address(&book.id);
        
        event::emit(AddressBookCreated {
            book_id,
            owner: sender,
        });

        transfer::transfer(book, sender);
    }

    /// Add a new encrypted contact to the address book
    /// Fails if contact with same key already exists
    public fun add_contact(
        book: &mut AddressBook,
        contact_key: String,
        encrypted_data: vector<u8>,
        nonce: vector<u8>,
        timestamp: u64,
    ) {
        // Validate key is not empty
        assert!(contact_key.length() > 0, EEmptyName);
        
        // Check if contact already exists
        assert!(!vec_map::contains(&book.contacts, &contact_key), EContactAlreadyExists);

        let contact = EncryptedContact {
            encrypted_data,
            nonce,
            created_at: timestamp,
            updated_at: timestamp,
        };

        vec_map::insert(&mut book.contacts, contact_key, contact);
        book.contact_count = book.contact_count + 1;

        event::emit(ContactAdded {
            book_id: object::uid_to_address(&book.id),
            contact_key,
        });
    }

    /// Update an existing contact's encrypted data
    /// Fails if contact doesn't exist
    public fun update_contact(
        book: &mut AddressBook,
        contact_key: String,
        encrypted_data: vector<u8>,
        nonce: vector<u8>,
        timestamp: u64,
    ) {
        // Check if contact exists
        assert!(vec_map::contains(&book.contacts, &contact_key), EContactNotFound);

        // Get mutable reference and update
        let contact = vec_map::get_mut(&mut book.contacts, &contact_key);
        contact.encrypted_data = encrypted_data;
        contact.nonce = nonce;
        contact.updated_at = timestamp;

        event::emit(ContactUpdated {
            book_id: object::uid_to_address(&book.id),
            contact_key,
        });
    }

    /// Remove a contact from the address book
    /// Storage rebate (99%) will be returned to the owner
    public fun remove_contact(
        book: &mut AddressBook,
        contact_key: String,
    ) {
        // Check if contact exists
        assert!(vec_map::contains(&book.contacts, &contact_key), EContactNotFound);

        // Remove the contact
        let (_key, _contact) = vec_map::remove(&mut book.contacts, &contact_key);
        book.contact_count = book.contact_count - 1;

        event::emit(ContactRemoved {
            book_id: object::uid_to_address(&book.id),
            contact_key,
        });
    }

    // ============================================================================
    // View Functions (for reading via RPC)
    // ============================================================================

    /// Get the number of contacts in the address book
    public fun get_contact_count(book: &AddressBook): u64 {
        book.contact_count
    }

    /// Check if a contact exists
    public fun has_contact(book: &AddressBook, contact_key: &String): bool {
        vec_map::contains(&book.contacts, contact_key)
    }

    /// Get encrypted contact data (returns copy)
    public fun get_contact(book: &AddressBook, contact_key: &String): (vector<u8>, vector<u8>) {
        assert!(vec_map::contains(&book.contacts, contact_key), EContactNotFound);
        let contact = vec_map::get(&book.contacts, contact_key);
        (contact.encrypted_data, contact.nonce)
    }

    /// Get all contact keys (for listing)
    public fun get_all_keys(book: &AddressBook): vector<String> {
        vec_map::keys(&book.contacts)
    }

    /// Get owner address
    public fun get_owner(book: &AddressBook): address {
        book.owner
    }
}
