import React, { useState, useEffect, useRef } from 'react';
import { useSignAndExecuteTransaction, useSuiClient } from '@mysten/dapp-kit';
import { Transaction } from '@mysten/sui/transactions';
import { sendChatMessage } from '../services/agentApi';
import CoinList from '../components/coins/CoinList';
import CoinMiniChart from '../components/coins/CoinMiniChart';

/**
 * AgentPage - AI Agent Chat interface with wallet transaction signing
 */
function AgentPage({ coins, userAddress }) {
    const [messages, setMessages] = useState([
        {
            id: 1,
            from: "agent",
            text: 'Welcome! I can help you with:\n• Check balance: "What is my SUI balance?"\n• Transfer: "Send 1 SUI to 0x..."\n• Address Book: "Create my address book"\n• Save contacts: "Save Alice 0x... as alice"',
            time: "now",
        },
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [pendingTransaction, setPendingTransaction] = useState(null);

    const chatRef = useRef(null);
    const suiClient = useSuiClient();
    const { mutateAsync: signAndExecute } = useSignAndExecuteTransaction();

    // Hover state for coin sidebar
    const [hoveredCoin, setHoveredCoin] = useState(null);
    const [hoverPos, setHoverPos] = useState({ x: 0, y: 0 });
    const leaveTimeoutRef = useRef(null);

    useEffect(() => {
        if (chatRef.current) {
            chatRef.current.scrollTop = chatRef.current.scrollHeight;
        }
    }, [messages]);

    const addMessage = (from, text, extra = {}) => {
        const msg = {
            id: Date.now() + Math.random(),
            from,
            text,
            time: new Date().toLocaleTimeString(),
            ...extra,
        };
        setMessages((prev) => [...prev, msg]);
        return msg;
    };

    /**
     * Build and execute a Move call transaction
     */
    const executeMoveCall = async (transactionData) => {
        console.log("executeMoveCall called with:", transactionData);

        const tx = new Transaction();

        // Parse arguments for the move call
        const args = (transactionData.arguments || []).map(arg => {
            if (typeof arg === 'object') {
                switch (arg.type) {
                    case 'object':
                        return tx.object(arg.value);
                    case 'string':
                        return tx.pure.string(arg.value);
                    case 'u64':
                        return tx.pure.u64(arg.value);
                    case 'vector_u8':
                        // Convert hex string to Uint8Array
                        const bytes = new Uint8Array(
                            arg.value.match(/.{1,2}/g)?.map(byte => parseInt(byte, 16)) || []
                        );
                        return tx.pure.vector('u8', Array.from(bytes));
                    default:
                        return arg.value;
                }
            }
            return arg;
        });

        console.log("Building moveCall with:", {
            target: transactionData.target,
            arguments: args,
            typeArguments: transactionData.type_arguments || []
        });

        // Add the move call
        tx.moveCall({
            target: transactionData.target,
            arguments: args,
            typeArguments: transactionData.type_arguments || [],
        });

        console.log("Calling signAndExecute...");

        // Sign and execute
        const result = await signAndExecute({
            transaction: tx,
        });

        console.log("signAndExecute result:", result);

        // Wait for transaction to be confirmed
        await suiClient.waitForTransaction({
            digest: result.digest,
        });

        console.log("Transaction confirmed!");

        return result;
    };

    /**
     * Build and execute a SUI transfer transaction
     */
    const executeTransfer = async (transactionData) => {
        const tx = new Transaction();

        // Convert amount to MIST (1 SUI = 1e9 MIST)
        const amountInMist = BigInt(transactionData.amount);

        // Split coins for the transfer
        const [coin] = tx.splitCoins(tx.gas, [amountInMist]);

        // Transfer to recipient
        tx.transferObjects([coin], transactionData.recipient);

        // Sign and execute
        const result = await signAndExecute({
            transaction: tx,
        });

        // Wait for confirmation
        await suiClient.waitForTransaction({
            digest: result.digest,
        });

        return result;
    };

    const sendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userText = input.trim();
        setInput("");

        // Add user message
        addMessage("user", userText);

        // Check wallet connection
        if (!userAddress) {
            addMessage("agent", "Please connect your wallet first to interact with the blockchain.");
            return;
        }

        setIsLoading(true);

        try {
            // Call backend API
            const response = await sendChatMessage(userText, userAddress);
            console.log("AI Response:", response);

            // Handle response based on intent
            if (response.intent) {
                const { action, parsed_data, clarification_question } = response.intent;

                if (action === "ambiguous" || clarification_question) {
                    // AI needs more info
                    addMessage("agent", response.message || clarification_question);
                }
                else if (action === "get_balance" && response.dry_run) {
                    // Balance query result
                    const balanceMsg = `Your ${response.dry_run.token || 'SUI'} balance: ${response.dry_run.balance_formatted || response.dry_run.current_balance}`;
                    addMessage("agent", balanceMsg);
                }
                else if (action === "transfer_token" && response.dry_run) {
                    // Transfer intent - show confirmation
                    const dryRun = response.dry_run;
                    const confirmMsg = `**Transfer Request**\n\n` +
                        `Amount: ${dryRun.amount_formatted || dryRun.amount} ${dryRun.token}\n` +
                        `To: ${dryRun.recipient?.slice(0, 10)}...${dryRun.recipient?.slice(-8)}\n` +
                        `Gas: ~${dryRun.estimated_gas_formatted || dryRun.estimated_gas} SUI\n\n` +
                        `Type "yes" to confirm the transfer.`;

                    addMessage("agent", confirmMsg, { type: "confirmation" });
                    setPendingTransaction({
                        ...response.transaction_data,
                        type: "transfer"
                    });
                }
                else if (action === "create_address_book") {
                    // Address book creation
                    console.log("CREATE_ADDRESS_BOOK intent received");
                    console.log("transaction_data:", response.transaction_data);

                    if (response.transaction_data) {
                        const confirmMsg = `**Create Address Book**\n\n` +
                            `This will create your personal on-chain address book.\n` +
                            `One-time setup, stored permanently on Sui.\n` +
                            `Estimated gas: ~0.01 SUI\n\n` +
                            `Type "yes" to confirm.`;

                        const txData = {
                            ...response.transaction_data,
                            type: "move_call"
                        };
                        console.log("Setting pendingTransaction:", txData);

                        addMessage("agent", confirmMsg, { type: "confirmation" });
                        setPendingTransaction(txData);
                    } else {
                        console.log("No transaction_data in response!");
                        addMessage("agent", response.message || "Ready to create your address book.");
                    }
                }
                else if (action === "save_contact") {
                    // Save contact to address book
                    if (response.transaction_data) {
                        const contactKey = response.transaction_data.contact_key;
                        const contactName = response.transaction_data.contact_name;

                        const confirmMsg = `**Save Contact**\n\n` +
                            `Name: ${contactName}\n` +
                            `Key: ${contactKey}\n` +
                            `Will be encrypted and stored on-chain.\n` +
                            `Estimated gas: ~0.02 SUI\n\n` +
                            `Type "yes" to confirm.`;

                        addMessage("agent", confirmMsg, { type: "confirmation" });
                        setPendingTransaction({
                            ...response.transaction_data,
                            type: "move_call"
                        });
                    } else {
                        addMessage("agent", response.message || "I need your address book ID to save contacts. Create one first with 'Create my address book'.");
                    }
                }
                else if (action === "list_contacts") {
                    // List contacts
                    addMessage("agent", response.message || "Your contacts will be listed here once you have an address book.");
                }
                else if (action === "resolve_contact") {
                    addMessage("agent", `Looking for contact: ${parsed_data?.name}. Contact not found in your address book.`);
                }
                else {
                    // Generic response
                    addMessage("agent", response.message || "I understood your request. How can I help further?");
                }
            } else if (response.message) {
                addMessage("agent", response.message);
            } else {
                addMessage("agent", "I received your message but couldn't process it. Please try again.");
            }
        } catch (error) {
            console.error("Chat error:", error);
            addMessage("agent", `Error: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();

            // Check for confirmation
            if (pendingTransaction && input.toLowerCase().trim() === "yes") {
                confirmTransaction();
            } else {
                sendMessage();
            }
        }
    };

    const confirmTransaction = async () => {
        if (!pendingTransaction) return;

        setInput("");
        addMessage("user", "yes");

        // Debug log
        console.log("=== EXECUTING TRANSACTION ===");
        console.log("Pending transaction:", JSON.stringify(pendingTransaction, null, 2));

        addMessage("agent", "Executing transaction... Please approve in your wallet.");
        setIsLoading(true);

        try {
            let result;

            if (pendingTransaction.type === "transfer") {
                console.log("Executing transfer...");
                result = await executeTransfer(pendingTransaction);
            } else if (pendingTransaction.type === "move_call" && pendingTransaction.target) {
                console.log("Executing move_call with target:", pendingTransaction.target);
                result = await executeMoveCall(pendingTransaction);
            } else {
                console.error("Unknown transaction type:", pendingTransaction.type);
                throw new Error(`Unknown transaction type: ${pendingTransaction.type}`);
            }

            console.log("Transaction result:", result);
            const digest = result.digest;
            addMessage("agent",
                `Transaction successful!\n\n` +
                `Digest: ${digest}\n\n` +
                `View on explorer:\nhttps://suiscan.xyz/testnet/tx/${digest}`
            );

        } catch (error) {
            console.error("Transaction error:", error);
            console.error("Error details:", {
                message: error.message,
                name: error.name,
                stack: error.stack
            });

            // Handle user rejection
            if (error.message?.includes('rejected') || error.message?.includes('cancelled')) {
                addMessage("agent", "Transaction cancelled by user.");
            } else {
                addMessage("agent", `Transaction failed: ${error.message}`);
            }
        } finally {
            setPendingTransaction(null);
            setIsLoading(false);
        }
    };

    // Coin hover handlers
    const handleCoinHover = (coin, rect) => {
        if (leaveTimeoutRef.current) {
            clearTimeout(leaveTimeoutRef.current);
            leaveTimeoutRef.current = null;
        }

        const GAP = 12;
        const x = rect.left - GAP;
        let y = rect.top + rect.height / 2;

        const viewportHeight = window.innerHeight;
        const ESTIMATED_HEIGHT = 240;
        const PADDING = 20;

        if (y + ESTIMATED_HEIGHT / 2 > viewportHeight - PADDING) {
            y = viewportHeight - ESTIMATED_HEIGHT / 2 - PADDING;
        }
        if (y - ESTIMATED_HEIGHT / 2 < PADDING) {
            y = ESTIMATED_HEIGHT / 2 + PADDING;
        }

        setHoveredCoin(coin);
        setHoverPos({ x, y });
    };

    const handleCoinLeave = () => {
        leaveTimeoutRef.current = setTimeout(() => {
            setHoveredCoin(null);
        }, 300);
    };

    const handlePopupEnter = () => {
        if (leaveTimeoutRef.current) {
            clearTimeout(leaveTimeoutRef.current);
            leaveTimeoutRef.current = null;
        }
    };

    const handlePopupLeave = () => {
        leaveTimeoutRef.current = setTimeout(() => {
            setHoveredCoin(null);
        }, 300);
    };

    return (
        <div className="agent-page">
            <div className="agent-main-column">
                <div className="agent-chat-header">
                    <h2 className="agent-title page-title--xl">AI Agent</h2>
                    <p>
                        Type a command and your agent will build Sui transactions from your prompt.
                    </p>
                    {!userAddress && (
                        <div style={{
                            background: 'rgba(255,200,0,0.1)',
                            border: '1px solid rgba(255,200,0,0.3)',
                            padding: '8px 12px',
                            borderRadius: '8px',
                            marginTop: '8px',
                            fontSize: '14px'
                        }}>
                            Connect your wallet to interact with the blockchain
                        </div>
                    )}
                </div>

                <div className="agent-chat-area" ref={chatRef}>
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`chat-bubble chat-bubble--${msg.from === "user" ? "user" : "agent"}`}
                        >
                            <div className="chat-bubble-meta">
                                <span className="chat-bubble-from">
                                    {msg.from === "user" ? "You" : "Agent"}
                                </span>
                                <span className="chat-bubble-time">{msg.time}</span>
                            </div>
                            <p className="chat-bubble-text" style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</p>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="chat-bubble chat-bubble--agent">
                            <div className="chat-bubble-meta">
                                <span className="chat-bubble-from">Agent</span>
                            </div>
                            <p className="chat-bubble-text">Thinking...</p>
                        </div>
                    )}
                </div>

                <div className="agent-input-bar">
                    <textarea
                        placeholder='Example: "Send 10 SUI to 0x..." or "Create my address book"'
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={isLoading}
                    />
                    <button
                        className="btn btn-primary"
                        onClick={pendingTransaction ? confirmTransaction : sendMessage}
                        disabled={isLoading}
                    >
                        {isLoading ? "..." : (pendingTransaction ? "Confirm" : "Send")}
                    </button>
                </div>
            </div>

            <div className="agent-coins-column">
                <h3 className="coins-title">Coins</h3>
                <p className="coins-subtitle">Hover to see the mini chart.</p>

                <div className="agent-coins-scroll">
                    <CoinList
                        coins={coins}
                        onHover={handleCoinHover}
                        onLeave={handleCoinLeave}
                    />
                </div>
            </div>

            {/* Global hover popup */}
            {hoveredCoin && (
                <div
                    className="coin-hover-layer"
                    style={{ top: hoverPos.y, left: hoverPos.x, pointerEvents: 'auto' }}
                    onMouseEnter={handlePopupEnter}
                    onMouseLeave={handlePopupLeave}
                >
                    <CoinMiniChart coin={hoveredCoin} />
                </div>
            )}
        </div>
    );
}

export default AgentPage;
