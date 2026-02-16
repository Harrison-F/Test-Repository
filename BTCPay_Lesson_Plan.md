# BTCPay Server Setup: Complete Merchant Guide
*Based on BTC Sessions Tutorial*

**Prerequisites:** Basic computer skills, Bitcoin wallet familiarity  
**Duration:** 2-3 hours setup + practice  
**Goal:** Accept Bitcoin payments (on-chain + Lightning) with automatic Liquid swaps

---

## Module 1: Introduction & Overview

**What You'll Build:**
- Self-hosted Bitcoin payment processor (no third-party custody)
- Accept on-chain Bitcoin payments
- Accept Lightning Network payments (instant, low fees)
- Automatic conversion to Liquid sidechain via Boltz plugin
- Custom store, donation page, and point-of-sale system
- TEST1234
**Key Benefits:**
- **Non-custodial:** You control your funds
- **Privacy:** No KYC required
- **Low fees:** ~$15.80/month hosting vs. 1-3% per transaction with processors
- **Professional:** Invoices, receipts, accounting tools

**Architecture Overview:**
- **LunaNode:** VPS hosting (accepts Bitcoin)
- **Bull Bitcoin:** Self-custody wallet (Canadian, supports Liquid)
- **BTCPay Server:** Open-source payment processor
- **Boltz Plugin:** Automatic submarine swaps to Liquid

---

## Module 2: LunaNode Setup (10 min)

**What You'll Do:** Deploy BTCPay Server on a VPS

### Step 2.1: Create LunaNode Account
1. Go to https://www.lunanode.com
2. Create account and add funds (accepts Bitcoin)
3. Navigate to API section

### Step 2.2: Create API Keys
1. Go to **API → Create API Key**
2. Note your **API ID** and **API Key**

### Step 2.3: Deploy BTCPay Server
1. Visit: https://launchbtcpay.lunanode.com
2. Enter your API ID and API Key
3. Click **Continue**
4. LunaNode will create a VM with BTCPay pre-installed (~$15.80/month)
5. Save the server IP address and credentials

### Step 2.4: Access BTCPay
1. Open browser: `http://YOUR-SERVER-IP`
2. Create admin account
3. You're now in the BTCPay dashboard

**Screenshot:** LunaNode BTCPay launcher interface showing API credentials fields and pricing.

---

## Module 3: Bull Bitcoin Wallet Setup (15 min)

**What You'll Do:** Connect your wallet to BTCPay

### Step 3.1: Create Bull Bitcoin Wallet
1. Download Bull Bitcoin wallet (mobile/desktop)
2. Sign up at https://app.bullbitcoin.com/registration/850620951575217852985155561438083230402263
3. Create a new wallet

### Step 3.2: Get Wallet Details
1. In Bull Bitcoin, go to **Wallet Settings**
2. Find:
   - **Extended Public Key (xpub)** — for receiving addresses
   - **Derivation Path** — typically `m/84'/0'/0'` (Native SegWit)
   - **Address Type** — Native SegWit (bc1... addresses)

### Step 3.3: Connect to BTCPay
1. In BTCPay, go to **Stores → Settings → Wallet**
2. Select **Setup wallet**
3. Choose **Enter extended public key manually**
4. Paste your xpub
5. Confirm derivation path: `m/84'/0'/0'`
6. Save

**Screenshot:** Bull Bitcoin wallet details screen showing xpub, derivation path, and address type.

**Links:**
- Bull Bitcoin Signup: https://app.bullbitcoin.com/registration/850620951575217852985155561438083230402263
- Bull Wallet Tutorial: https://youtu.be/s4fbc9naWj4

---

## Module 4: Create Your Store (10 min)

**What You'll Do:** Set up products and payment methods

### Step 4.1: Create Store
1. In BTCPay: **Stores → Create Store**
2. Name your store
3. Set **Default Currency:** USD
4. Set **Price Source:** Kraken (or your preferred exchange)

### Step 4.2: Configure Payment Methods
1. Go to **Checkout Experience**
2. Set payment method preferences:
   - **BTC-LN (Lightning):** Enable for amounts > $6.15
   - **BTC-CHAIN (On-chain):** Enable for amounts > $25
3. Configure checkout appearance:
   - Show timer (invoice expiration)
   - Display in Satoshis option
   - "Pay in wallet" button

**Screenshot:** BTCPay checkout settings showing payment method thresholds and customization options.

---

## Module 5: Lightning Network Setup (15 min)

**What You'll Do:** Enable instant Bitcoin payments

### Step 5.1: Enable Lightning
1. Go to **Stores → Settings → Lightning**
2. Click **Setup Lightning node**
3. Choose implementation:
   - **LND** (most common)
   - **Core Lightning (CLN)**
4. BTCPay will create and manage the node

### Step 5.2: Get Inbound Liquidity
Lightning requires **inbound liquidity** to receive payments:

**Options:**
1. **Open a channel:** Deposit Bitcoin to open a payment channel
2. **Use liquidity service:** Buy inbound liquidity (e.g., LNBIG, LightningPool)
3. **Request inbound:** Ask someone to open a channel to you

**Recommendation for merchants:** Start with $100-500 in a channel, increase as needed.

### Step 5.3: Test Lightning
1. Create a test invoice in BTCPay
2. Pay it with a Lightning wallet (e.g., Bull Bitcoin, Phoenix, Breez)
3. Payment should confirm instantly

**Key Concept:** Lightning payments are instant but require channel liquidity. On-chain works for any amount but takes 10-60 minutes to confirm.

---

## Module 6: Boltz Plugin — Automatic Liquid Swaps (15 min)

**What You'll Do:** Automatically convert Lightning payments to Liquid sidechain

### Step 6.1: Why Liquid?
- **Faster settlements:** 1-minute blocks vs. 10-minute Bitcoin blocks
- **Lower fees:** For small frequent payments
- **Privacy:** Confidential Transactions hide amounts
- **Interoperability:** Swap back to Bitcoin anytime

### Step 6.2: Install Boltz Plugin
1. In BTCPay: **Server Settings → Plugins**
2. Search for **"Boltz"**
3. Install **Boltz Client Plugin**
4. Restart BTCPay if required

### Step 6.3: Configure Auto-Swaps
1. Go to **Stores → Boltz**
2. Enable **Automatic Swaps**
3. Set thresholds:
   - **Minimum swap amount:** 0.001 BTC (~$50)
   - **Maximum swap amount:** 0.1 BTC (~$5,000)
4. Set **Target:** Liquid sidechain
5. Save settings

### Step 6.4: How It Works
- When you receive a Lightning payment above the threshold
- Boltz automatically swaps it to Liquid
- Funds appear in your Liquid wallet within minutes
- You hold Liquid L-BTC (pegged 1:1 to Bitcoin)

**Links:**
- Boltz Plugin: https://boltz.exchange

---

## Module 7: Store Customization & POS (15 min)

**What You'll Do:** Create customer-facing interfaces

### Step 7.1: Customize Store Appearance
1. Go to **Stores → Settings → Checkout Appearance**
2. Upload logo
3. Set brand colors
4. Add custom CSS (optional)

### Step 7.2: Create Products
1. Go to **Products**
2. Click **Create Product**
3. Add:
   - Name and description
   - Price (fixed or variable)
   - Image
   - Inventory tracking (optional)
4. Save

### Step 7.3: Set Up Point of Sale (POS)
1. Go to **Apps → Point of Sale**
2. Create new POS
3. Add products to categories
4. Configure:
   - Quick-tap buttons for common amounts
   - Tips (optional)
   - Receipt printing (optional)
5. Save and bookmark the POS URL

### Step 7.4: Create Donation Page
1. Go to **Apps → Crowdfund**
2. Create a campaign
3. Set goal (optional)
4. Customize message
5. Share the donation URL

---

## Module 8: Go Live & Best Practices (10 min)

### Step 8.1: Security Checklist
- [ ] Change default admin password
- [ ] Enable 2FA (Two-Factor Authentication)
- [ ] Set up backup email
- [ ] Configure email notifications for payments
- [ ] Set up webhook notifications (optional)

### Step 8.2: Backup Strategy
1. **Wallet backup:** Write down seed phrase from Bull Bitcoin
2. **BTCPay backup:**
   - Go to **Server Settings → Maintenance → Backup**
   - Download backup file
   - Store securely (encrypted USB, password manager)
3. **Lightning backup:**
   - Go to **Lightning → Channels → Export**
   - Save channel backup file

### Step 8.3: Accounting & Reporting
1. Go to **Invoices** to see all payments
2. Export to CSV for accounting software
3. Set up automated exports (optional)

### Step 8.4: Test Everything
- [ ] Create test on-chain invoice
- [ ] Create test Lightning invoice
- [ ] Verify payments appear in wallet
- [ ] Check Boltz swaps (if enabled)
- [ ] Test POS interface

---

## Quick Reference: Common Tasks

| Task | Path |
|------|------|
| Create invoice | Stores → Invoices → Create |
| View payments | Stores → Invoices |
| Add product | Stores → Products → Create |
| Configure Lightning | Stores → Settings → Lightning |
| Manage wallet | Stores → Settings → Wallet |
| POS interface | Apps → Point of Sale |
| Donation page | Apps → Crowdfund |
| Backup data | Server Settings → Maintenance |

---

## Resources & Links

**Official Documentation:**
- BTCPay Docs: https://docs.btcpayserver.org
- LunaNode Guide: https://www.lunanode.com/guides/btcpay

**Video References:**
- Main Tutorial: https://www.youtube.com/watch?v=4boOmhAB3bo
- Bull Wallet Tutorial: https://youtu.be/s4fbc9naWj4
- Coldcard Tutorial: https://youtu.be/InDyHPcgNdk

**Support:**
- BTCMentor (paid help): https://btcmentor.io
- BTCPay Telegram: https://t.me/btcpayserver

**Hardware:**
- Buy Coldcard: https://qrco.de/bfiDBV
- Coldcard Tutorial: https://youtu.be/InDyHPcgNdk

---

## Practice Exercises

1. **Invoice Test:** Create 3 test invoices ($5, $50, $500) and pay them
2. **Lightning Flow:** Receive via Lightning, watch auto-swap to Liquid (if enabled)
3. **Store Build:** Build a 5-product store with categories
4. **POS Demo:** Simulate a retail transaction
5. **Backup Test:** Restore BTCPay from backup (on test server)

---

**Questions or issues?** Refer to the official BTCPay documentation or contact support via the links above.
