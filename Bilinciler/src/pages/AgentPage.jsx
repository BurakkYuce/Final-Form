import React, { useState, useEffect, useRef } from 'react';
import { useSignAndExecuteTransaction, useSuiClient } from '@mysten/dapp-kit';
import { Transaction } from '@mysten/sui/transactions';
import { sendChatMessage } from '../services/agentApi';
import CoinList from '../components/coins/CoinList';
import CoinMiniChart from '../components/coins/CoinMiniChart';
import TransactionQueue from '../components/TransactionQueue';

/**
 * AgentPage - AI Agent Chat interface with wallet transaction signing
 */
function AgentPage({ coins, userAddress }) {
    const [messages, setMessages] = useState([
        {
            id: 1,
            from: "agent",
            text: 'Welcome! I can help you with:\n• Check balance: "What is my SUI balance?"\n• Transfer: "Send 1 SUI to 0x..."\n• Staking: "Stake 5 SUI" or "Unstake 2 SUI"\n• Check stake: "How much do I have staked?"\n• Address Book: "Create my address book"\n• Save contacts: "Save Alice 0x... as alice"',
            time: "now",
        },
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [transactionQueue, setTransactionQueue] = useState([]);

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
                    // Transfer intent - add to queue
                    const dryRun = response.dry_run;
                    const queueMsg = `Added transfer to queue:\n` +
                        `${dryRun.amount_formatted || dryRun.amount} ${dryRun.token} -> ${dryRun.recipient?.slice(0, 6)}...`;

                    addMessage("agent", queueMsg); // Inform user
                    setTransactionQueue(prev => [...prev, {
                        ...response.transaction_data,
                        type: "transfer",
                        // Store formatting info for UI
                        amount_formatted: dryRun.amount_formatted,
                        token: dryRun.token,
                        recipient: dryRun.recipient
                    }]);
                }
                else if (action === "create_address_book") {
                    if (response.transaction_data) {
                        addMessage("agent", "Added 'Create Address Book' to transaction queue.");
                        setTransactionQueue(prev => [...prev, {
                            ...response.transaction_data,
                            type: "move_call",
                            function_name: "create_address_book"
                        }]);
                    } else {
                        addMessage("agent", response.message || "Ready to create your address book.");
                    }
                }
                else if (action === "save_contact") {
                    if (response.transaction_data) {
                        addMessage("agent", `Added 'Save Contact: ${response.transaction_data.contact_name}' to queue.`);
                        setTransactionQueue(prev => [...prev, {
                            ...response.transaction_data,
                            type: "move_call",
                            function_name: "add_contact"
                        }]);
                    } else {
                        addMessage("agent", response.message || "I need your address book ID to save contacts.");
                    }
                }
                else if (action === "stake_token") {
                    // Stake intent - add to queue
                    if (response.transaction_data) {
                        const txData = response.transaction_data;
                        const amountInSui = (txData.amount / 1e9).toFixed(4);
                        addMessage("agent", `Added stake transaction to queue: ${amountInSui} SUI`);
                        setTransactionQueue(prev => [...prev, {
                            ...txData,
                            type: "stake"
                        }]);
                    } else {
                        addMessage("agent", response.message || "Ready to stake SUI.");
                    }
                }
                else if (action === "unstake_token") {
                    // Unstake intent - add to queue
                    if (response.transaction_data) {
                        const txData = response.transaction_data;
                        const amountInSui = (txData.amount / 1e9).toFixed(4);
                        addMessage("agent", `Added unstake transaction to queue: ${amountInSui} SUI`);
                        setTransactionQueue(prev => [...prev, {
                            ...txData,
                            type: "unstake"
                        }]);
                    } else {
                        addMessage("agent", response.message || "Ready to unstake SUI.");
                    }
                }
                else if (action === "get_stake_info") {
                    // Stake info query - display result
                    addMessage("agent", response.message || "Stake information retrieved.");
                }
                else if (action === "list_contacts") {
                    addMessage("agent", response.message || "Your contacts will be listed here once you have an address book.");
                }
                else if (action === "resolve_contact") {
                    addMessage("agent", `Limit reached or contact not found: ${parsed_data?.name}.`);
                }
                else {
                    addMessage("agent", response.message || "I understood your request. How can I help further?");
                }
            } else if (response.message) {
                addMessage("agent", response.message);
            } else {
                addMessage("agent", "I received your message buf couldn't process it.");
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


            // Standard send
            sendMessage();
        }
    };

    /**
     * Execute all queued transactions as a single Programmable Transaction Block (PTB)
     */
    const executeBatch = async () => {
        if (!transactionQueue.length) return;

        console.log("=== EXECUTING BATCH ===");
        addMessage("agent", "Building batch transaction... Please sign in your wallet.");
        setIsLoading(true);

        try {
            const tx = new Transaction();

            // Iterate over queue and add commands to the PTB
            for (const item of transactionQueue) {
                if (item.type === "transfer") {
                    // --- Transfer logic ---
                    const amountInMist = BigInt(item.amount);
                    const [coin] = tx.splitCoins(tx.gas, [amountInMist]);
                    tx.transferObjects([coin], item.recipient);
                }
                else if (item.type === "stake") {
                    // --- Stake logic ---
                    const amountInMist = BigInt(item.amount);
                    const [coinToStake] = tx.splitCoins(tx.gas, [amountInMist]);
                    tx.moveCall({
                        target: item.target,
                        arguments: [
                            tx.object(item.stake_pool_id),
                            coinToStake
                        ]
                    });
                }
                else if (item.type === "unstake") {
                    // --- Unstake logic ---
                    const amountInMist = BigInt(item.amount);
                    tx.moveCall({
                        target: item.target,
                        arguments: [
                            tx.object(item.stake_pool_id),
                            tx.pure.u64(amountInMist)
                        ]
                    });
                }
                else if (item.type === "move_call") {
                    // --- Move Call logic ---
                    const args = (item.arguments || []).map(arg => {
                        if (typeof arg === 'object') {
                            switch (arg.type) {
                                case 'object': return tx.object(arg.value);
                                case 'string': return tx.pure.string(arg.value);
                                case 'u64': return tx.pure.u64(arg.value);
                                case 'vector_u8':
                                    const bytes = new Uint8Array(
                                        arg.value.match(/.{1,2}/g)?.map(byte => parseInt(byte, 16)) || []
                                    );
                                    return tx.pure.vector('u8', Array.from(bytes));
                                default: return arg.value;
                            }
                        }
                        return arg;
                    });

                    tx.moveCall({
                        target: item.target,
                        arguments: args,
                        typeArguments: item.type_arguments || [],
                    });
                }
            }

            // Execute the single PTB
            const result = await signAndExecute({
                transaction: tx,
            });

            console.log("Batch Execution Result:", result);

            // Wait for confirmation
            await suiClient.waitForTransaction({ digest: result.digest });

            addMessage("agent",
                `Batch executed successfully!\nDigest: ${result.digest}\n\n` +
                `https://suiscan.xyz/testnet/tx/${result.digest}`
            );

            // Clear queue on success
            setTransactionQueue([]);

        } catch (error) {
            console.error("Batch Execution Error:", error);
            if (error.message?.includes('rejected')) {
                addMessage("agent", "Transaction flow cancelled.");
            } else {
                addMessage("agent", `Execution failed: ${error.message}`);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const removeTransactionFromQueue = (index) => {
        setTransactionQueue(prev => prev.filter((_, i) => i !== index));
    };

    const clearQueue = () => {
        setTransactionQueue([]);
        addMessage("agent", "Transaction queue cleared.", { type: "system" });
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
                        onClick={sendMessage}
                        disabled={isLoading}
                    >
                        {isLoading ? "..." : "Send"}
                    </button>
                </div>
            </div>

            <div className="agent-coins-column">
                <TransactionQueue
                    queue={transactionQueue}
                    onExecute={executeBatch}
                    onClear={clearQueue}
                    onRemove={removeTransactionFromQueue}
                    isLoading={isLoading}
                />

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
