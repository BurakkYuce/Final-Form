import express from "express";
import bodyParser from "body-parser";
import { SuiClient, getFullnodeUrl } from "@mysten/sui/client";
import { Transaction } from "@mysten/sui/transactions";
import { bcs } from "@mysten/sui/bcs";
import { fromBase64 } from "@mysten/sui/utils";

// ======================
// CONFIG
// ======================
const client = new SuiClient({ url: getFullnodeUrl("testnet") });

const STAKE_PACKAGE_ID = "0x...SENIN_PKG_ID...";
const STAKE_MODULE = "stake";
const STAKE_POOL_OBJECT_ID = "0x...SENIN_POOL_ID...";

const app = express();
app.use(bodyParser.json());

// ======================
// GET /stake/info
// ======================
app.get("/stake/info", async (req, res) => {
    try {
        const obj = await client.getObject({
            id: STAKE_POOL_OBJECT_ID,
            options: { showContent: true },
        });

        const content = obj.data?.content as any;
        
        // Move struct'ında `balance: Balance<SUI>` olduğu için 
        // balance bir obje olarak görünmeyebilir, dynamic field olabilir 
        // veya direkt fields içinde 'balance' değeri (u64) olarak görünebilir.
        // Genelde Balance struct'ı { value: u64 } tutar.
        const balanceStruct = content?.fields?.balance; 
        const totalStaked = balanceStruct ? Number(balanceStruct) : 0; 
        // Not: Balance struct'ı bazen direkt value döndürür, bazen obje. 
        // Testnet'te publish edip field yapısına bakmak gerekir.

        res.json({
            poolId: STAKE_POOL_OBJECT_ID,
            totalStaked,
        });
    } catch (e: any) {
        res.status(500).json({ error: e.message });
    }
});

// ======================
// GET /stake/position/:address
// DevInspect ile okuma
// ======================
app.get("/stake/position/:address", async (req, res) => {
    const userAddress = req.params.address;
    try {
        const tx = new Transaction();
        tx.moveCall({
            target: `${STAKE_PACKAGE_ID}::${STAKE_MODULE}::get_user_stake`,
            arguments: [
                tx.object(STAKE_POOL_OBJECT_ID),
                tx.pure.address(userAddress),
            ],
        });

        const inspect = await client.devInspectTransactionBlock({
            sender: userAddress,
            transactionBlock: tx,
        });

        // Yeni SDK'da return value okuma:
        if (inspect.results && inspect.results[0].returnValues) {
            const rawValue = inspect.results[0].returnValues[0];
            // rawValue = [bytes, typeString]
            const bytes = Uint8Array.from(rawValue[0]);
            
            // Move u64 -> JS BigInt -> Number
            // bcs.u64() kullanarak parse ediyoruz
            const stakedAmount = bcs.u64().parse(bytes);
            
            return res.json({ userAddress, staked: Number(stakedAmount) });
        }

        res.json({ userAddress, staked: 0 });
    } catch (e: any) {
        res.status(500).json({ error: e.message });
    }
});

// ======================
// POST /stake/build
// ======================
app.post("/stake/build", async (req, res) => {
    const { sender, amount } = req.body;
    if (!sender || !amount) return res.status(400).json({ error: "Eksik parametre" });

    try {
        const tx = new Transaction();
        tx.setSender(sender);

        // ÖNEMLİ: Stake fonksiyonu Coin<SUI> bekliyor.
        // Kullanıcının Gas coininden (SUI) belirtilen miktarı bölüp (split)
        // o yeni coini fonksiyona yolluyoruz.
        
        const [coinToStake] = tx.splitCoins(tx.gas, [tx.pure.u64(amount)]);

        tx.moveCall({
            target: `${STAKE_PACKAGE_ID}::${STAKE_MODULE}::stake`,
            arguments: [
                tx.object(STAKE_POOL_OBJECT_ID),
                coinToStake, // Oluşturduğumuz coin
            ],
        });

        // Base64 serialize
        const txBytes = await tx.build({ client: client });
        const txBase64 = Buffer.from(txBytes).toString("base64");

        res.json({ txBytesBase64: txBase64 });
    } catch (e: any) {
        console.error(e);
        res.status(500).json({ error: e.message });
    }
});

// ======================
// POST /unstake/build
// ======================
app.post("/unstake/build", async (req, res) => {
    const { sender, amount } = req.body;
    if (!sender || !amount) return res.status(400).json({ error: "Eksik parametre" });

    try {
        const tx = new Transaction();
        tx.setSender(sender);

        // Unstake sadece miktar (u64) bekliyor
        tx.moveCall({
            target: `${STAKE_PACKAGE_ID}::${STAKE_MODULE}::unstake`,
            arguments: [
                tx.object(STAKE_POOL_OBJECT_ID),
                tx.pure.u64(amount),
            ],
        });

        const txBytes = await tx.build({ client: client });
        const txBase64 = Buffer.from(txBytes).toString("base64");

        res.json({ txBytesBase64: txBase64 });
    } catch (e: any) {
        console.error(e);
        res.status(500).json({ error: e.message });
    }
});

app.listen(4000, () => console.log("Backend running on 4000"));