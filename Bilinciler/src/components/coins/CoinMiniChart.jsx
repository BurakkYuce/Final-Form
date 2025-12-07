import React, { useState, useEffect } from 'react';
import { getChartColor, normalizeDataToPoints, generateFakeSparkline, generateFakeHistoryData } from '../../utils/coinHelpers';

function CoinMiniChart({ coin }) {
    const [activeRange, setActiveRange] = useState("1M");
    const [chartData, setChartData] = useState(coin.sparkline || []);

    useEffect(() => {
        setActiveRange("1M");
    }, [coin.symbol]);

    useEffect(() => {
        if (activeRange === "1D") {
            setChartData(coin.sparkline || generateFakeSparkline(coin.change24h));
        } else {
            setChartData(generateFakeHistoryData(activeRange, coin.price));
        }
    }, [activeRange, coin]);

    const firstVal = chartData[0] || 0;
    const lastVal = chartData[chartData.length - 1] || 0;
    const change = activeRange === "1D" ? coin.change24h : ((lastVal - firstVal) / firstVal) * 100;
    const color = getChartColor(change);

    const width = 260;
    const height = 80;

    const points = normalizeDataToPoints(chartData, width, height);
    const polylinePoints = points.map(p => `${p.x},${p.y}`).join(" ");

    const ranges = ["1D", "1W", "1M", "1Y", "ALL"];

    return (
        <div className="coin-popup-inner" style={{ minWidth: 280, padding: 16 }}>
            <div className="coin-popup-header" style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontWeight: 'bold', fontSize: '1.1em' }}>{coin.name} ({coin.symbol})</span>
                    <span style={{ fontSize: '0.85em', opacity: 0.7 }}>{activeRange} Trend</span>
                </div>
                <div style={{ textAlign: 'right' }}>
                    <div style={{ color, fontWeight: 'bold', fontSize: '1.1em' }}>${coin.price.toLocaleString()}</div>
                    <div style={{ fontSize: '0.85em', color }}>
                        {change >= 0 ? "+" : ""}{change.toFixed(2)}%
                    </div>
                </div>
            </div>

            <div className="coin-popup-body" style={{ marginBottom: 12, display: 'flex', justifyContent: 'center' }}>
                <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto", maxWidth: "100%", overflow: "visible" }}>
                    <polyline
                        points={polylinePoints}
                        fill="none"
                        stroke={color}
                        strokeWidth="3"
                    />
                    {points.map((p, i) => (
                        <circle
                            key={i}
                            cx={p.x}
                            cy={p.y}
                            r="3"
                            fill={color}
                        />
                    ))}
                </svg>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, background: 'rgba(255,255,255,0.05)', borderRadius: 6, padding: 4 }}>
                {ranges.map(r => (
                    <button
                        key={r}
                        className={`btn btn-sm ${activeRange === r ? 'btn-primary' : 'btn-ghost'}`}
                        onClick={(e) => {
                            e.stopPropagation();
                            setActiveRange(r);
                        }}
                        style={{
                            padding: '4px 8px',
                            fontSize: '11px',
                            minWidth: 'unset',
                            height: '24px',
                            borderRadius: 4
                        }}
                    >
                        {r}
                    </button>
                ))}
            </div>
        </div>
    );
}

export default CoinMiniChart;
