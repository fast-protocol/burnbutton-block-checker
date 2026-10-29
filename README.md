# BurnButton Protocol — Smart Contract Block-Checker v1.0

Official open-source infrastructure utility and security tool built for the BNB Chain ecosystem to address the silent block-time drift vulnerability outlined in **Community Issue #133**.

## Live Production Tool
👉 **Live Web Interface:** [https://checker.burnbutton.xyz](https://checker.burnbutton.xyz)

---

## 1. The Core Vulnerability (Issue #133)
Historically, BNB Chain (BSC) operated with a fixed block generation time of **3.0 seconds**. Legacy smart contracts (vesting calendars, liquidity locks, staking epochs) frequently hardcoded block counts (`block.number`) to measure real-world time.

Following recent network upgrades, block time has been heavily optimized down to **~0.45 seconds**. Consequently, block-measured time limits expire **~6.67x faster** than intended by the developers (e.g., a 1-year token lock releases in just ~54 days), creating severe systemic economic risks.

---

## 2. Technical Architecture & Analysis Framework
This tool operates as an automated, non-custodial express-auditor consisting of two unified layers:

* **Backend Engine (Python HTTP Server):** Leverages Etherscan API V2 multi-chain gateways to instantly pull verified smart contract source codes directly from the BNB Chain ledger. It utilizes precision Abstract Syntax Tree (AST) patterns and regex mapping to audit low-level environments.
* **Frontend Dashboard (Vercel Production UI):** A lightweight, low-latency responsive interface styled in the core BurnButton cyberpunk neon palette.

### Scanned Vulnerability Vector Matrix:
1. **Block-Time Shift Risk:** Detects `block.number`, Yul/Assembly `number()`, and `blockhash()` opcodes. Calculates the precise drift factor based on the current block rate.
2. **Contract Erasure Backdoors:** Scans for high-risk malicious `selfdestruct` or `suicide` methods that allow developers to wipe contracts and execute rugpulls.
3. **DeFi Protection Layer:** Evaluates contract logic for critical missing `nonReentrant` state locks or unmitigated `tx.origin` phishing pathways.

---

## 3. Production Deployment Structure
* `checker.py` — High-performance, asynchronous Python handler with built-in native CORS resolution and Chromium browser spoofing headers to bypass Cloudflare edge limits.
* `index.html` — Vanilla JavaScript reactive client executing unified asynchronous `fetch` actions.
