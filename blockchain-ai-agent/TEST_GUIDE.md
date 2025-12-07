# Test Rehberi - Gerçek Transaction Testi

## ✅ Hazırlık Tamamlandı!

Tüm servisler yazıldı ve test edildi:
- ✅ Wallet Service (gerçek transaction imzalama)
- ✅ OpenAI Integration (AI intent parsing)
- ✅ Walrus Storage (encrypted contacts)
- ✅ Seal Encryption (privacy-first)
- ✅ Sui Blockchain (PTB transactions)

## 🚀 Test Adımları

### 1. Serveri Başlat

```bash
cd C:\Users\byrock\Desktop\a\blockchain-ai-agent
python main.py
```

Veya:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Test Suite'i Çalıştır

**YENİ Terminal Aç:**
```bash
cd C:\Users\byrock\Desktop\a\blockchain-ai-agent
python test_real_transactions.py
```

### 3. Test Sonuçları

Test suite şunları test edecek:

1. **Health Check** - Server sağlığı
2. **Balance Check** - OpenAI ile bakiye sorgusu
3. **Save Contact** - Walrus'a encrypted contact kaydetme
4. **List Contacts** - Seal ile decryption
5. **Transfer Intent** - AI ile transfer niyeti parse etme
6. **Disambiguation** - Belirsiz intent handling
7. **REAL Transaction** - Gerçek Sui blockchain transaction! 💰

### 4. Gerçek Transaction

Test suite, gerçek transaction yapmadan önce onay soracak:

```
WARNING: The next test will execute a REAL transaction on Sui testnet
Amount: 0.01 SUI + gas fees
Do you want to execute the real transaction test? (yes/no):
```

**"yes"** yazarsan:
- Cüzdan 1'den Cüzdan 2'ye **0.01 SUI** gönderilecek
- Gerçek transaction digest alacaksın
- Sui Explorer'da görebileceksin

## 📊 Cüzdan Bilgileri

**Cüzdan 1 (Gönderen):**
- Address: `0x6d6ea71aeb3029760347ecee4cd7472af79a7d9ec1c9205ef123e726206aec69`
- Balance: **1.0 SUI** ✅
- Role: Sender

**Cüzdan 2 (Alıcı):**
- Address: `0x6e0d6daf2309688ce56606e72fca267ae25f36d43d9d27ccf324f96d7e6e7e07`
- Balance: **1.0 SUI** ✅
- Role: Recipient

## 🎯 Beklenen Sonuçlar

### Test 1-6: BAŞARILI ✅
Tüm testler geçmeli:
- OpenAI API çağrıları çalışmalı
- Walrus upload/download çalışmalı
- Contact encryption/decryption çalışmalı

### Test 7: Gerçek Transaction
```json
{
  "success": true,
  "transaction_digest": "0x...",
  "effects": {
    "status": "success",
    "gas_used": "...",
    "events": 0
  }
}
```

**Explorer Link:**
```
https://testnet.suivision.xyz/txblock/TRANSACTION_DIGEST
```

## 💡 Manuel Test (Opsiyonel)

Eğer test suite kullanmak istemezsen, manuel olarak da test edebilirsin:

### 1. Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### 2. Balance Check
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my SUI balance?",
    "user_address": "0x6d6ea71aeb3029760347ecee4cd7472af79a7d9ec1c9205ef123e726206aec69"
  }'
```

### 3. Gerçek Transfer
```bash
curl -X POST "http://localhost:8000/api/v1/execute?private_key=suiprivkey1qzw4ak32zhgnn25ns2taccem79dnqhzm3z6hy2370f84cefnf837qltw4pn" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_data": {
      "action": "transfer_token",
      "recipient": "0x6e0d6daf2309688ce56606e72fca267ae25f36d43d9d27ccf324f96d7e6e7e07",
      "amount": "10000000",
      "token": "SUI"
    },
    "user_address": "0x6d6ea71aeb3029760347ecee4cd7472af79a7d9ec1c9205ef123e726206aec69"
  }'
```

## ⚠️ Önemli Notlar

1. **Private Key Güvenliği:** Test için private key URL'de gönderiliyor. Production'da bu ASLA yapılmamalı!

2. **Gas Fees:** Her transaction ~0.001-0.01 SUI gas fee alır

3. **Testnet:** Şu anda testnet üzerinde çalışıyoruz, gerçek SUI değil

4. **OpenAI Maliyeti:** Her AI çağrısı ~$0.01 OpenAI credit kullanır

## 📝 Test Sonrası

Transaction başarılıysa:
- ✅ Cüzdan 1 bakiyesi: ~0.99 SUI olmalı
- ✅ Cüzdan 2 bakiyesi: ~1.01 SUI olmalı
- ✅ Explorer'da transaction görünmeli

## 🎉 Başarı Kriteri

Tüm testler geçerse:
```
Total: 7 tests
Passed: 7
Failed: 0
Skipped: 0

🎉 ALL TESTS PASSED! 🎉
```

## 🔍 Hata Durumunda

Eğer bir test başarısız olursa:
1. Server loglarını kontrol et
2. OpenAI API key'in geçerli mi kontrol et
3. Sui testnet RPC erişilebilir mi kontrol et
4. Walrus testnet çalışıyor mu kontrol et

---

**Hazır mısın? Testi başlat!**

```bash
python test_real_transactions.py
```
