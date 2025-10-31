# Public-Subsidy-Transparency-Ledger-Simulated-Variant-
# 🪙 Public Subsidy Transparency Ledger (PSTL)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green)
![MongoDB](https://img.shields.io/badge/Database-MongoDB-darkgreen)
![License](https://img.shields.io/badge/License-View--Only-lightgrey)
![Status](https://img.shields.io/badge/Status-In%20Progress-yellow)

**Blockchain + AI for Transparent and Accountable Governance**

The **Public Subsidy Transparency Ledger (PSTL)** is a prototype framework that combines **blockchain simulation**, **AI-based anomaly detection**, and **open data visualization** to bring radical transparency to government subsidy distribution.

It simulates the end-to-end flow of funds — **Central → State → District → Beneficiary** — recording each transaction as an **immutable ledger event** and using intelligent models to detect irregularities, leakages, or misuse in real time.

---

## 🧭 Vision

To create a **“Glass Government”** ecosystem — where public funds are **traceable, auditable, and tamper-proof**, ensuring benefits reach the intended citizens with minimal corruption or inefficiency.

---

## ⚙️ System Architecture

```
Central Govt ──► State Govt ──► District Admin ──► Beneficiary
     │               │               │                  │
     └───────────────┴───────────────┴──────────────────┘
                      ▼ Event Logs
            ┌────────────────────────────┐
            │ Blockchain Ledger (Foundry)│
            └────────────────────────────┘
                      ▼
            ┌────────────────────────────┐
            │      MongoDB Store         │
            └────────────────────────────┘
                      ▼
            ┌────────────────────────────┐
            │   FastAPI Orchestrator     │
            └────────────────────────────┘
                      ▼
            ┌────────────────────────────┐
            │ AI / ML Anomaly Detection  │
            └────────────────────────────┘
                      ▼
            ┌────────────────────────────┐
            │ Public Dashboard (React)   │
            └────────────────────────────┘
```

### 🧩 Layer Breakdown

Layer	Technology	Purpose
Simulated Ledger Layer	Foundry (Rust)	Emulates an immutable blockchain ledger with modular block finalization.
Database Layer	MongoDB	Stores hierarchical subsidy transactions and anomaly metadata.
Backend API	FastAPI (Python)	Handles event ingestion, validation, anomaly detection, and REST endpoints.
Analytics Layer	Scikit-learn / Pandas	Detects anomalies and predicts fund leakage risks.
Frontend (Planned)	React + Tailwind	Visual dashboard for transparency and citizen access.


---

## 🚀 Features

- 🪙 **Immutable Event Logging** — Every subsidy transaction is cryptographically recorded  
- 🧠 **AI-Driven Anomaly Detection** — Flags suspicious fund flow patterns  
- 🗂️ **Hierarchical Flow Simulation** — Tracks distribution across administrative levels  
- 🔍 **Open Data APIs** — REST endpoints for analytics, integration, and visualization  
- 🌐 **Transparency Dashboard (Planned)** — Visual interface for public and auditors  

---

## 🧰 Tech Stack

Category	Tools / Frameworks
Blockchain Simulation	Foundry (Rust)
Backend	FastAPI (Python)
Database	MongoDB
AI / ML	Scikit-learn, Pandas, NumPy
Frontend (Planned)	React, Tailwind CSS
Containerization	Docker (optional)

---

## 📦 Project Structure

```
PSTL/
│
├── backend/
│   ├── main.py                # FastAPI entrypoint
│   ├── routes/                # API endpoints
│   ├── services/              # Anomaly detection & logic
│   └── models/                # MongoDB schemas
│
├── ledger/
│   ├── contracts/             # Foundry-based Rust ledger simulation
│   ├── events/                # Transaction event definitions
│   └── utils/                 # Blockchain helpers
│
├── frontend/ (planned)
│   └── src/                   # React + Tailwind dashboard
│
├── data/
│   └── seed_data.json         # Synthetic PM-KISAN-like dataset
│
├── LICENSE
└── README.md
```

---

## 🧪 Quick Start (Development Setup)

### 1️⃣ Clone Repository
```bash
git clone https://github.com/<your-username>/Public-Subsidy-Transparency-Ledger.git
cd Public-Subsidy-Transparency-Ledger
```

### 2️⃣ Setup Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3️⃣ Run Ledger Simulator
```bash
cd ledger
cargo run
```

### 4️⃣ Access API Docs
FastAPI provides an auto-generated Swagger UI at  
👉 **http://127.0.0.1:8000/docs**

---

## 📊 Sample API Routes

Method	Endpoint	Description
POST	/ingest/event	Record new subsidy transaction event
GET	/transactions	Fetch all logged events
GET	/anomalies	View flagged transactions
GET	/stats/overview	Get aggregated transparency metrics

---

## 🧠 AI & Anomaly Detection Overview

The anomaly detection layer uses:
- **Z-score & Isolation Forests** for statistical outlier detection  
- **Temporal flow analysis** to catch irregular fund timing  
- **Pattern matching** across administrative hierarchies  

All predictions are logged back into MongoDB and surfaced via API or dashboard.

---

## 🔮 Future Roadmap

Phase	Focus	Key Deliverables
Phase 1 (MVP)	Ledger + Backend + Mock Data	Complete core FastAPI orchestration with Foundry simulation
Phase 2	AI Integration	Implement and tune anomaly models
Phase 3	Dashboard	Develop public visualization dashboard
Phase 4	Testnet Deployment	Connect to real blockchain or civic data feeds

---

## 🧾 License

This project is protected under a **Custom View-Only License**.  
> Permission is granted to **view, read, and reference** the source code for **educational and non-commercial purposes only**.  
> Modification, redistribution, or derivative works are **strictly prohibited** without explicit written consent from the author.

---

## 👤 Author

**Smit Kagathara**  
Developer & Researcher — CivicTech, Blockchain, and AI Systems  
🔗 [GitHub Profile](https://github.com/your-username)  
📧 [smitkagathara@zohomail.in]

---

## ⭐ Acknowledgements

Special thanks to the **Open Data and GovTech** community for inspiring a transparent future of governance, and to the **FastAPI** and **Foundry** ecosystems for their incredible developer tools.

---

> *“Transparency is not just about access — it’s about accountability.”*


