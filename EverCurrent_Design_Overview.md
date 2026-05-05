# EverCurrent: Enterprise Engineering Intelligence Platform

## 1. Architecture: Relational Scaling
To handle a global hardware portfolio, the system is designed around a **Relational Data Model**, moving beyond simple "list-based" summarization.

### A. The Project Registry (Metadata Store)
Unlike basic tools, our architecture decouples the **Project State** from the user. Each project in the database carries its own metadata:
*   **Stage:** (Concept, EVT, DVT, PVT, MP).
*   **Knowledge Context:** Links to specific CAD repositories and Technical Specs.

### B. Identity Source of Truth (`users.json`)
In real Slack workspaces, usernames are opaque (`alex.johnson`, `a.j.2024`) and carry **no role information**. Our system resolves identity through a dedicated lookup:

```
Slack username  →  users.json lookup  →  Role + Department + Projects
"alex.johnson"  →  Identity Store     →  "Mechanical Engineer", Engineering, [Battery B-800, Chassis C-200]
```

*   **Prototype:** Static `users.json` file with `username → role` mapping.
*   **Production:** **Okta / Active Directory via SCIM**, which syncs `slack_user_id → role + department` automatically when org structure changes.

This means role-based prioritization, privacy filtering, and access control all work **without relying on username conventions** — a production-grade requirement.


### B. The 3D Priority Matrix (Role x Topic x Phase)
Relevance is calculated using a multidimensional intersection:
*   **Role Lens:** (Finance, Engineering, Marketing, Supply Chain).
*   **Project Phase:** (A "CAD Change" is critical in EVT but an 'Alert' in PVT).
*   **Topic Density:** (The "Heat" of the conversation).

## 2. The Knowledge Backbone (Source-of-Truth RAG)
The system connects to a **Technical Knowledge Base** (RAG) to ensure accuracy. It cross-references Slack discussions against official Spec Sheets, 2D Drawings, and ECNs from the PLM system.

## 3. From Prototype to Production (The Scaling Plan)

| Component | **Prototype (MVP)** | **Production (Scaling)** |
| :--- | :--- | :--- |
| **Identity & Roles** | Static `users.json` role doc. | **Okta / Active Directory** with dynamic role & stakeholder mapping. |
| **Knowledge Base** | `Technical_Knowledge_Base/` folder. | **Enterprise RAG Pipeline** syncing with Arena PLM, Jira, and Drive. |
| **Processing** | Sequential Python script. | **Asynchronous Task Queue** (Celery/Redis) for high throughput. |
| **AI Ingest** | Mock Slack JSON. | **Real-time Webhooks** with stream processing (Kafka/RabbitMQ). |
| **The "Brain"** | Local Llama 3 (Ollama). | **Private GPU Clusters (vLLM)** with fine-tuned engineering models. |
| **Data Security** | Local execution. | **On-Prem or VPC Deployment** for SOC2/IP Protection. |

## 4. Intelligent Process Triggers
The system acts as a "Process Sentinel," flagging when a formal intervention is needed:
*   **Sprint Trigger:** High density of blockers in a 24h window.
*   **Design Review Trigger:** Conflicting technical sentiment in a long thread.
*   **Design Debt Alert:** Scans for hardware workaround language (e.g., "shim").

> **Architectural Note:** These triggers are implemented as pure, deterministic Python heuristics (keyword matching and density counting). They execute instantly (<1ms) and completely bypass the LLM. This decouples instant UI alerting from the slower generative AI summarization layer, saving compute cycles for tasks that actually require semantic reasoning.

## 5. Cross-Functional Translation Layer
The **Agentic Reasoning Engine** performs cross-functional translation:
*   **To Finance:** Translates technical failures into **"CAPEX Risk"** or **"Unit Cost Variance."**
*   **To Engineering:** Translates the same failures into **"Design Violations"** or **"Blockers."**

## 6. Noise Filtering & Communication Health

### Message Noise Categories
Real Slack workspaces contain significant non-project traffic. The system classifies and **routes all noise away from the digest** before it reaches the user:

| Category | Examples | Routing |
| :--- | :--- | :--- |
| `Off-Topic` | Lunch plans, sports chat | Score = 0, filtered panel only |
| `Platform/IT` | Slack outages, upload failures, 403 errors | Score = 0, filtered panel + IT log |
| `HR/Admin` | Performance review reminders, all-hands | Score = 0, filtered panel only |
| `Access Management` | Vendor losing Slack Connect, token expiry | Score = 0, triggers Vendor Access Alert |

The LLM classifier is explicitly trained (via prompt) to recognize these categories. Pre-tagged `noise_type` fields in mock data bypass the LLM call entirely for efficiency.

### Vendor Access Monitoring (`Vendor_Access_Status.json`)
External partners (Slack Connect) can lose access due to token expiry, IT resets, or account changes. A separate silo tracks:
*   **Status:** `active` or `degraded` per vendor channel
*   **Last Seen Timestamp:** Detect silence > 48h as a potential access loss
*   **Invite Status:** `accepted` or `expired`
*   **Fallback Contact:** Email/phone for out-of-band communication when Slack fails

In production, this would be backed by the **Slack Admin API** for real-time invite status checks.

## 6. Prompt Engineering & AI Guardrails

### Prototype (Demo)
The current implementation uses **zero-shot instruction prompts** — the AI is told what to do via text (e.g., "do not mention internal cost figures"). This is sufficient for a demonstration but is inherently fragile:
- Smaller models (Llama3:8b) can occasionally "leak" restricted content despite instructions
- Instruction-following degrades with prompt complexity

### Production Requirements

| Layer | Mechanism | Purpose |
| :--- | :--- | :--- |
| **Pre-LLM Filter** | Strip restricted data from context *before* it reaches the model | Structural guarantee — AI can't reveal what it never sees |
| **Output Scanner** | Regex + secondary LLM scans response for financial figures, vendor names, part numbers | Catch leakage before it reaches the user |
| **Prompt Fine-Tuning** | Few-shot examples of correct internal vs. vendor summaries baked into the prompt | Consistent, domain-specific output quality |
| **RLHF** | Engineers rate outputs; model learns what "good" looks like for hardware engineering | Continuous improvement loop |
| **Domain Fine-Tuning** | Fine-tune on actual engineering Slack/PLM data | Model understands jargon without re-explanation |
| **Audit Logging** | Hash + log every AI response in vendor sessions | IP leak traceability and compliance |

> **Key Principle:** In production, the safest guardrail is *never sending restricted data to the LLM at all* — structural filtering beats instruction-following every time.

---

## 8. Production Roadmap

### Feature 1: Customer-Configurable Scoring Engine

**Current State (Prototype):**
The 3D weighting matrix (`Role × Topic × Phase`) is hardcoded by the developer. All EverCurrent customers use the same weights.

**Problem:**
A hardware robotics startup and an automotive OEM have fundamentally different notions of what "CAD/Design" means to a Finance manager in DVT. One-size-fits-all weights produce wrong priorities for real customers.

**Production Solution:**
Expose the scoring matrix as a **customer-configurable admin interface**:

- Org admins can tune weights per `Role × Topic × Phase` cell via a dashboard UI
- Industry presets (Hardware, Pharma, Automotive, Software) ship as starting templates
- Weight configurations stored per-org in the database — not hardcoded
- A/B testing: run two scoring configurations in parallel, measure which surfaces more actionable threads

**Implementation:**
```
ScoreConfig (DB Table)
├── org_id
├── role
├── topic
├── phase
└── weight  ← admin-editable, defaults to industry preset
```

---

### Feature 2: Multi-Document Confidentiality Classification

**Current State (Prototype):**
Privacy is enforced at the **role level** only — Internal vs. Vendor. We test one engineering spec and one finance policy document.

**Problem:**
In production, a knowledge base contains dozens of document types with **varying sensitivity levels** that do not map cleanly to role tiers:

| Document Type | Example | Sensitivity |
| :--- | :--- | :--- |
| Engineering spec | `B800_Battery_Spec.txt` | Internal (Engineering + QA) |
| CAD drawing PDF | `Rev3_Baseplate.pdf` | Internal (Engineering only) |
| Budget spreadsheet | `Q2_Hardware_Budget.xlsx` | Restricted (Finance + Exec) |
| Supplier contract | `TMCorp_NDA_2026.pdf` | Restricted (Legal + Exec) |
| HR policy | `PTO_Policy.pdf` | Internal (All employees) |
| Vendor spec sheet | `HarmonicDrive_H40_Datasheet.pdf` | Shareable (Vendor-scoped) |

**Production Solution:**
Add **document-level sensitivity tags** on top of the current role-level filter:

```
Document Sensitivity Schema:
├── doc_id
├── doc_type            (spec, cad, budget, contract, policy, vendor_sheet)
├── sensitivity_level   (public, internal, restricted, confidential)
├── allowed_roles       [list of roles that can access]
└── allowed_projects    [scope to specific projects if needed]
```

The `load_ground_truth()` function then filters by **both** the user's role AND the document's sensitivity tag before injecting into the LLM context — two independent gates.

**Test Coverage Needed (Future):**
- Budget spreadsheet injected into Finance session → verify figures appear
- Same budget injected into Vendor session → verify complete block
- CAD PDF injected into Vendor session → verify block even though spec sheet is allowed
- Supplier contract injected into Engineering session → verify block (Legal/Exec only)
