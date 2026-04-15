# System Architecture

## Overview

The Public Subsidy Transparency Ledger (PSTL) is a government transparency platform that tracks subsidy programs, projects, and disbursements with full audit trails and AI-powered anomaly detection.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React 18)                     │
│  Dashboard | SubsidyList | PublicTransparency | Analytics  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  Routes | Schemas | Validation | Security                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                             │
│  SubsidyService | AnalyticsService | AnomalyDetection      │
│  RiskEngine | FundFlowService | FraudNetwork               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  SQLAlchemy ORM                             │
│  PostgreSQL Database with ACID compliance                  │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### Domain Models
- **User** - Authentication and role assignment
- **Role** - Government roles (Public, Media, Auditor, GovernmentOfficial, Admin)
- **Subsidy** - Government subsidy programs with risk/transparency scores
- **Project** - Projects funded by subsidies
- **Disbursement** - Fund transfer records
- **AuditRecord** - Immutable audit trail
- **RiskEvent** - Detected anomalies and risk events
- **ScoringHistory** - Historical risk/transparency score tracking

### API Endpoints
- `/auth/*` - Authentication (login, register)
- `/subsidies/*` - Subsidy CRUD operations
- `/projects/*` - Project management
- `/disbursements/*` - Fund disbursement tracking
- `/audits/*` - Audit trail access
- `/analytics/*` - Dashboard analytics, anomaly detection, fund flow
- `/public/*` - Public transparency portal (no auth required)

### Security
- JWT-based authentication
- Role-based access control (RBAC)
- Permission decorators (`require_roles`, `require_permission`)

### AI/Analytics Features
- **Risk Scoring** - 0-100 score based on multiple factors
- **Transparency Scoring** - Based on record completeness
- **Anomaly Detection** - Z-score analysis, pattern detection
- **Fraud Network Analysis** - Graph-based relationship analysis
- **Fund Flow Visualization** - Track funds from subsidy → project → disbursement

## Data Flow

1. **Subsidy Creation** → GovernmentOfficial creates subsidy → AuditRecord created
2. **Project Assignment** → Subsidy linked to projects
3. **Disbursement** → Funds released → Risk engine evaluates → Anomaly detection runs
4. **Analytics** → Real-time dashboards, risk distribution, sector analysis
5. **Public Access** → Anyone can view transparency portal without login

## Blockchain Integration

The system supports optional blockchain proof recording via `backend/ai/blockchain_service.py` for immutable audit verification.
