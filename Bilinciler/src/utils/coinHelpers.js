// CoinMarketCap API helpers and chart utilities

export const CMC_ENDPOINT =
    "/api/v1/cryptocurrency/listings/latest?start=1&limit=50&convert=USD";

export function formatBigNumber(n) {
    if (!n && n !== 0) return "—";
    if (n >= 1e12) return (n / 1e12).toFixed(2) + "T";
    if (n >= 1e9) return (n / 1e9).toFixed(2) + "B";
    if (n >= 1e6) return (n / 1e6).toFixed(2) + "M";
    if (n >= 1e3) return (n / 1e3).toFixed(2) + "K";
    return n.toFixed(2);
}

export function generateFakeSparkline(change24h = 0) {
    const base = 50;
    const steps = 8;
    const slope = change24h / steps;
    const arr = [];

    for (let i = 0; i < steps; i++) {
        const v = base + slope * i;
        arr.push(Math.max(10, Math.min(90, v)));
    }

    return arr;
}

export function generateFakeHistoryData(range, basePrice) {
    let steps = 20;
    let volatility = 0.05;

    switch (range) {
        case "1D": steps = 24; volatility = 0.02; break;
        case "1W": steps = 7; volatility = 0.05; break;
        case "1M": steps = 30; volatility = 0.10; break;
        case "1Y": steps = 12; volatility = 0.20; break;
        case "ALL": steps = 50; volatility = 0.50; break;
    }

    const arr = [];
    let current = basePrice;

    for (let i = 0; i < steps; i++) {
        const change = (Math.random() - 0.5) * volatility;
        current = current * (1 + change);
        arr.push(current);
    }
    return arr;
}

export function getChartColor(change) {
    return change >= 0 ? "#10b981" : "#ef4444";
}

export function normalizeDataToPoints(data, width, height) {
    if (!data || data.length === 0) return [];

    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;

    const stepX = width / (data.length - 1);

    const points = data.map((val, i) => {
        const x = i * stepX;
        const normalizedY = (val - min) / range;
        const y = height - normalizedY * height;
        return { x, y, val };
    });

    return points;
}

export function mapCMCToCoin(coin) {
    const quote = coin.quote?.USD || {};
    return {
        id: coin.id,
        name: coin.name,
        symbol: coin.symbol,
        logo: `https://s2.coinmarketcap.com/static/img/coins/64x64/${coin.id}.png`,
        price: quote.price || 0,
        change24h: quote.percent_change_24h || 0,
        change7d: quote.percent_change_7d || 0,
        marketCap: formatBigNumber(quote.market_cap),
        volume24h: formatBigNumber(quote.volume_24h),
        dominance: (quote.market_cap_dominance || 0).toFixed(1) + "%",
        circulatingSupply: formatBigNumber(coin.circulating_supply) + " " + coin.symbol,
        sparkline: generateFakeSparkline(quote.percent_change_24h || 0),
        holdings: null,
    };
}

export async function fetchCoinsFromCMC() {
    try {
        const response = await fetch(CMC_ENDPOINT, {
            headers: {
                "X-CMC_PRO_API_KEY": import.meta.env.VITE_CMC_API_KEY,
            },
        });

        if (!response.ok) {
            console.error("CMC API ERROR:", response.status, await response.text());
            return [];
        }

        const data = await response.json();
        return data.data.map(mapCMCToCoin);
    } catch (err) {
        console.error("CMC FETCH ERROR:", err);
        return [];
    }
}
