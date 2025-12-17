# 🪙 Public Subsidy Transparency Ledger (PSTL) — Simulated Variant

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green)
![MongoDB](https://img.shields.io/badge/Database-MongoDB-darkgreen)
![License](https://img.shields.io/badge/License-View--Only-lightgrey)
![Status](https://img.shields.io/badge/Status-Active%20Development-yellow)

**A simulated transparency framework for tracking public subsidy flows using ledger-style immutability and AI-assisted audits.**

---

## 📌 Project Overview

The **Public Subsidy Transparency Ledger (PSTL)** is a **backend-first prototype** that simulates how government subsidies can be transparently tracked across administrative levels — from **Central Authority to Beneficiaries**.

Instead of a live blockchain, PSTL uses a **ledger-style event model** combined with **tamper-resistant logging, audit trails, and anomaly detection** to demonstrate how transparency, traceability, and accountability can be engineered into public fund distribution systems.

This project is built as a **modular FastAPI backend** with clear separation between:

* Ledger events
* Business rules
* Audit logic
* Anomaly detection
* Data persistence

---

## 🎯 Core Objective

To design and implement a **proof-of-concept system** that shows how public subsidy disbursement can be:

* 🔍 Fully traceable
* 🧾 Auditable at every level
* 🚨 Automatically flagged for irregularities
* 🌐 Exposed via open APIs for dashboards or public access

---

## 🧠 What This Project Is (and Isn’t)

✔ **Is**

* A realistic backend simulation of subsidy flows
* A ledger-inspired event system (append-only, auditable)
* A foundation for AI-based anomaly detection
* A strong academic + engineering prototype

✖ **Is Not**

* A production blockchain network
* A real government data pipeline
* A financial transaction system

(That honesty alone saves you from awkward viva questions.)

---

## ⚙️ Updated System Architecture

```
Client / Admin / Auditor
        │
        ▼
┌────────────────────────────┐
│        FastAPI API         │
│  (Routes + Validation)    │
└────────────────────────────┘
        │
        ▼
┌────────────────────────────┐
│   Service Layer Logic      │
│  - Subsidy Lifecycle      │
│  - Disbursement Rules     │
│  - Ledger Event Builder   │
│  - Audit Triggers         │
└────────────────────────────┘
        │
        ▼
┌────────────────────────────┐
│   Immutable Ledger Tables  │
│  (Append-only records)     │
│  - Transactions           │
│  - Events                 │
│  - Audit Logs             │
└────────────────────────────┘
        │
        ▼
┌────────────────────────────┐
│  Relational Database       │
│ (PostgreSQL / SQLite)      │
│  - ACID guarantees        │
│  - Referential integrity  │
└────────────────────────────┘
        │
        ▼
┌────────────────────────────┐
│ AI / Anomaly Detection    │
│ - Statistical checks      │
│ - Pattern analysis        │
│ - Risk scoring            │
└────────────────────────────┘

```

---

## 🧩 Implemented Modules (Current State)

### 🔹 Ledger Simulation

* Event-based transaction recording
* Append-only ledger model
* Each subsidy movement logged as a discrete event
* Supports traceability across hierarchy levels

### 🔹 Backend API (FastAPI)

* RESTful endpoints for:

  * Subsidy creation
  * Disbursement tracking
  * Ledger queries
  * Audit & anomaly retrieval
* Pydantic-based validation
* Modular route design

### 🔹 Database Layer (MongoDB)

* Hierarchical transaction storage
* Ledger event persistence
* Audit & anomaly metadata storage

### 🔹 Anomaly Detection (In Progress)

* Rule-based red flags (amount thresholds, timing gaps)
* Statistical methods (Z-score)
* ML-ready structure (Isolation Forest extensible)

---

## 🧰 Tech Stack

| Layer          | Technology                 | Role                                 |
| -------------- | -------------------------- | ------------------------------------ |
| Backend        | FastAPI (Python)           | API orchestration & validation       |
| Database       | MongoDB                    | Ledger events, audits, metadata      |
| Ledger Model   | Simulated Event Ledger     | Immutable-style transaction tracking |
| AI / Analytics | Pandas, Scikit-learn       | Anomaly detection & risk scoring     |
| Frontend       | React + Tailwind (Planned) | Transparency dashboard               |
| Dev Tools      | Docker (Optional)          | Containerized deployment             |

---

## 📂 Updated Project Structure

```
PSTL/
│
├── backend/
│   ├── main.py                     # FastAPI application entrypoint
│   ├── database/
│   │   └── connection.py           # MongoDB connection handler
│   │
│   ├── models/
│   │   ├── base.py                 # Shared schema fields
│   │   ├── subsidy.py              # Subsidy master data
│   │   ├── project.py              # Government projects
│   │   ├── disbursement.py         # Fund flow records
│   │   └── role.py                 # Actor roles (Central, State, etc.)
│   │
│   ├── routes/
│   │   ├── subsidy_routes.py
│   │   ├── disbursement_routes.py
│   │   ├── audit_routes.py
│   │   └── analytics_routes.py
│   │
│   ├── services/
│   │   ├── ledger_service.py       # Ledger event generation
│   │   ├── audit_service.py        # Audit logic
│   │   └── anomaly_service.py      # Detection algorithms
│   │
│   └── utils/
│       └── helpers.py
│
├── data/
│   └── seed_data.json               # Synthetic subsidy dataset
│
├── frontend/ (planned)
│
├── LICENSE
└── README.md
```

---

## 🚀 Running the Project (Local)

### 1️⃣ Clone

```bash
git clone https://github.com/<your-username>/Public-Subsidy-Transparency-Ledger.git
cd Public-Subsidy-Transparency-Ledger
```

### 2️⃣ Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3️⃣ API Documentation

Swagger UI available at:

```
http://127.0.0.1:8000/docs
```

---

## 📊 Key API Endpoints

| Method | Endpoint           | Description                  |
| ------ | ------------------ | ---------------------------- |
| POST   | /subsidy           | Create subsidy scheme        |
| POST   | /disbursement      | Record fund transfer         |
| GET    | /ledger            | View immutable ledger events |
| GET    | /audit             | Fetch audit trail            |
| GET    | /anomalies         | View flagged transactions    |
| GET    | /analytics/summary | Transparency metrics         |

---

## 🧠 Anomaly Detection Logic (Current)

* Unusual fund amount deviations
* Abnormal disbursement frequency
* Skipped hierarchy levels
* Repeated beneficiary patterns

Designed to be **explainable**, not magical — because auditors hate black boxes.

---

## 🔮 Planned Enhancements

| Phase   | Focus                                     |
| ------- | ----------------------------------------- |
| Phase 1 | Complete backend + ledger stability       |
| Phase 2 | Strengthen anomaly detection models       |
| Phase 3 | Public transparency dashboard             |
| Phase 4 | Optional blockchain / testnet integration |

---

## 🧾 License

**All Rights Reserved – View Only**

You may **view and reference** this repository for **educational purposes only**.
Copying, modifying, or redistributing any part of the codebase without permission is prohibited.

---

## 👤 Author

**Smit Kagathara**
Developer | CivicTech • Backend Systems • Transparency Engineering
📧 Contact: *smitkagathara@zohomail.in*
🔗 GitHub: *github.com/Smit-whitespace*

---

## 💬 Final Thought

> *“Transparency isn’t about revealing everything — it’s about making wrongdoing impossible to hide.”*
