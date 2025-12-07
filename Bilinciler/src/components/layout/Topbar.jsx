import React from 'react';

function Topbar({ wallet, onConnectWallet, theme, onToggleTheme, onGoogleLogin, enokiAddress }) {
    return (
        <header className="topbar">
            <div className="topbar-left">
                <h1 className="topbar-title">AI-Powered Sui Console</h1>
                <p className="topbar-subtitle">
                    Give natural language commands. Let your agent handle the on-chain work.
                </p>
            </div>
            <div className="topbar-right">
                <button className="btn btn-ghost theme-toggle" onClick={onToggleTheme}>
                    {theme === "dark" ? "Light mode" : "Dark mode"}
                </button>
                <div className="topbar-wallet">
                    {enokiAddress ? (
                        <div className="wallet-info" style={{ marginRight: '10px' }}>
                            <span className="wallet-balance" style={{ fontSize: '10px', color: '#999' }}>zkLogin</span>
                            <span className="wallet-address" title={enokiAddress}>
                                {enokiAddress.slice(0, 4)}...{enokiAddress.slice(-4)}
                            </span>
                        </div>
                    ) : (
                        <button
                            onClick={onGoogleLogin}
                            className="btn btn-secondary"
                            style={{
                                marginRight: '10px',
                                fontSize: '18px',
                                padding: '14px 20px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px'
                            }}
                        >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M21.35 11.1h-9.17v2.73h6.51c-.33 3.8-3.5 5.44-6.5 5.44C8.36 19.27 5 16.25 5 12c0-4.1 3.2-7.27 7.2-7.27 3.09 0 4.9 1.97 4.9 1.97L19 4.72S16.56 2 12.1 2C6.42 2 2.03 6.8 2.03 12c0 5.05 4.13 10 10.22 10 5.35 0 9.25-3.67 9.25-9.09 0-1.15-.15-1.81-.15-1.81z" />
                            </svg>
                            Sign in with Google
                        </button>
                    )}

                    {wallet.connected ? (
                        <>
                            <div className="wallet-info">
                                <span className="wallet-address">
                                    {wallet.address.slice(0, 4)}...{wallet.address.slice(-4)}
                                </span>
                                <span className="wallet-balance">
                                    {wallet.suiBalance.toFixed(2)} SUI
                                </span>
                            </div>
                            <button className="btn btn-ghost" onClick={onConnectWallet}>
                                Disconnect
                            </button>
                        </>
                    ) : (
                        <button className="btn btn-primary" onClick={onConnectWallet}>
                            Connect Wallet
                        </button>
                    )}
                </div>
            </div>
        </header>
    );
}

export default Topbar;
