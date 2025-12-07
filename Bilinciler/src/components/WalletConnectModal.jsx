import React from "react";
import { useWallets, useConnectWallet, useDisconnectWallet, useCurrentAccount } from "@mysten/dapp-kit";

export function WalletConnectModal({ isOpen, onClose }) {
    const wallets = useWallets(); // Tüm cüzdan listesi
    const { mutate: connect, isPending: isConnecting } = useConnectWallet();
    const { mutate: disconnect } = useDisconnectWallet();
    const account = useCurrentAccount(); // Şu anki bağlı hesap

    if (!isOpen) return null;

    const shortAddress = account?.address
        ? account.address.slice(0, 4) + "..." + account.address.slice(-4)
        : "";

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2 className="modal-title">Cüzdan Bağla</h2>
                    <button className="modal-close" onClick={onClose}>
                        ✕
                    </button>
                </div>

                {account ? (
                    <div className="wallet-section">
                        <div className="wallet-connected-card">
                            <span className="wallet-label">Bağlı Cüzdan</span>
                            <span className="wallet-address-display">{shortAddress}</span>
                            <span className="wallet-provider-name">Aktif Hesap</span>
                        </div>

                        <button
                            onClick={() => {
                                disconnect();
                                // Opsiyonel: Disconnect sonrası modalı kapatmak isterseniz:
                                // onClose(); 
                            }}
                            className="btn btn-secondary"
                            style={{ borderColor: '#ef4444', color: '#ef4444', background: 'rgba(239, 68, 68, 0.1)' }}
                        >
                            Bağlantıyı Kes
                        </button>
                    </div>
                ) : (
                    <div className="wallet-section">
                        <p style={{ fontSize: '13px', color: 'var(--text-soft)', margin: 0 }}>
                            Aşağıdan bir Sui cüzdanı seçerek bağlanın.
                        </p>

                        <div className="wallet-list">
                            {wallets.length === 0 && (
                                <div style={{ fontSize: '13px', color: '#ef4444', padding: '10px' }}>
                                    Uyumlu cüzdan bulunamadı. Sui Wallet, Suiet veya benzeri bir eklenti kurduğunuzdan emin olun.
                                </div>
                            )}

                            {wallets.map((wallet) => (
                                <button
                                    key={wallet.name}
                                    onClick={() => connect({ wallet })}
                                    disabled={isConnecting}
                                    className="wallet-item"
                                >
                                    <div className="wallet-icon-name">
                                        {wallet.icon && (
                                            <img
                                                src={wallet.icon}
                                                alt={wallet.name}
                                                className="wallet-icon"
                                            />
                                        )}
                                        <span>{wallet.name}</span>
                                    </div>
                                    <span style={{ fontSize: '12px', color: 'var(--text-soft)' }}>
                                        {isConnecting ? "..." : "Bağlan"}
                                    </span>
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
