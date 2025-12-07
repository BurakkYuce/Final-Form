import React from 'react';
import { PAGES } from '../../constants/pages';

function Sidebar({ activePage, onChangePage }) {
    const items = [
        { key: PAGES.AGENT, label: "AI Agent" },
        { key: PAGES.COINS, label: "Coins" },
        { key: PAGES.STAKING, label: "Staking" },
        { key: PAGES.HISTORY, label: "History" },
        { key: PAGES.WALLET, label: "Wallet" },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <img src="/logo.png" alt="Bilinciler Logo" className="sidebar-logo-img" />
                <div className="sidebar-logo-text">
                    <span>Sui Agent</span>
                    <small>AI Transaction Hub</small>
                </div>
            </div>

            <nav className="sidebar-nav">
                {items.map((item) => (
                    <button
                        key={item.key}
                        className={
                            "sidebar-nav-item" +
                            (activePage === item.key ? " sidebar-nav-item--active" : "")
                        }
                        onClick={() => onChangePage(item.key)}
                    >
                        <span>{item.label}</span>
                    </button>
                ))}
            </nav>

            <div className="sidebar-footer">
                <span className="sidebar-badge">Sui • Dev / Test</span>
            </div>
        </aside>
    );
}

export default Sidebar;
