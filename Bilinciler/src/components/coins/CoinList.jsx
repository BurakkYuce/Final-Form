import React from 'react';

function CoinList({ coins, onHover, onLeave }) {
    return (
        <div className="coin-list coin-list--sidebar">
            {coins.map((coin) => (
                <div
                    key={coin.symbol}
                    className="coin-row"
                    onMouseEnter={(e) => {
                        if (!onHover) return;
                        const rect = e.currentTarget.getBoundingClientRect();
                        onHover(coin, rect);
                    }}
                    onMouseLeave={onLeave}
                >
                    <div className="coin-row-left">
                        {coin.logo ? (
                            <img
                                src={coin.logo}
                                alt={coin.name}
                                className="coin-logo-img"
                                style={{ width: 30, height: 30, marginRight: 12 }}
                                onError={(e) => {
                                    e.target.style.display = "none";
                                    e.target.nextSibling.style.display = "flex";
                                }}
                            />
                        ) : null}
                        <div
                            className="coin-avatar"
                            style={{ display: coin.logo ? "none" : "flex" }}
                        >
                            {coin.symbol[0]}
                        </div>
                        <div>
                            <div className="coin-name">{coin.name}</div>
                            <div className="coin-price">
                                ${coin.price.toLocaleString()}
                            </div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}

export default CoinList;
