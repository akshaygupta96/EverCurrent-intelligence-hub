# EverCurrent: Engineering Intelligence Hub

**An Agentic Reasoning Engine for Hardware Portfolio Management.**

This platform eliminates communication silos by aggregating Slack, meeting transcripts, and technical specifications into a single, phase-aware daily digest. It is designed to ensure that critical technical risks (e.g., thermal violations) are identified and translated for cross-functional stakeholders (Engineering, Finance, PMs, External Partners) in real-time.

---

## Key Features

- **Phase-Aware 3D Prioritization:** Dynamically re-ranks threads based on `Role x Topic x Project Phase`. A "Logistics Delay" is noise for a MechE in EVT but a blocker for Finance in PVT.
- **Thread Aggregation:** x`Groups multi-message Slack conversations into unified threads with a density bonus, so hot debates surface automatically.
- **LLM Topic Classification:** Uses Llama 3 to semantically classify messages — no fragile keyword matching.
- **Source-of-Truth RAG:** Grounds AI summaries in official Technical Specs and Meeting Decisions before answering.
- **Process Triggers:** Automatically recommends Design Reviews or Sprints based on conversation volume and blocker language.
- **Design Debt Detection:** Scans threads for hardware workaround language (e.g., "shim," "zip-tie," "for now") and fires a Design Debt Alert, prompting the team to log an Engineering Change Order (ECO) before design freeze.
- **BOM-Drift Detection (Conceptual):** Identifies discrepancies between Slack chatter (e.g., "switching to the H40 actuator due to lead times") and the static Project Registry, alerting the team to unrecorded Engineering Change Orders before the BOM diverges from physical reality.
- **Privacy & Redaction Layer:** External Partners are blocked from internal silos. The AI is dynamically instructed to redact proprietary data from their summaries.

---

## Getting Started

### Prerequisites

- Python 3.10+
- **Ollama** running locally with `llama3` pulled:
  ```bash
  ollama pull llama3
  ```

### Setup & Run

```bash
# 1. Activate the virtual environment
.\venv\Scripts\Activate.ps1        # Windows
source venv/bin/activate            # Mac/Linux

# 2. Install dependencies (first time only)
pip install streamlit requests

# 3. Generate the enterprise mock data
python generate_enterprise_data.py

# 4. Launch the dashboard
streamlit run app.py
```

---

## Tech Stack

### Prototype / Demo

| Layer                    | Tool / Library        | Purpose                                                           |
| :----------------------- | :-------------------- | :---------------------------------------------------------------- |
| **UI**             | `Streamlit`         | Interactive dashboard                                             |
| **LLM Runtime**    | `Ollama` (local)    | Runs Llama3 on-device — no cloud API, no IP leakage              |
| **LLM Model**      | `Llama3:8b` (Meta)  | Topic classification, RAG synthesis, role-specific interpretation |
| **HTTP Client**    | `requests`          | Calls Ollama REST API at `localhost:11434`                      |
| **Data Store**     | `JSON` flat files   | Mock Slack messages, project registry, 3D weighting matrix        |
| **Identity Store** | `users.json`        | Static user role & project assignment doc                         |
| **PDF Parsing**    | `pypdf` (installed) | Ready for real spec sheet ingestion                               |
| **Language**       | `Python 3.10+`      | Core application logic                                            |

### Methods & Approaches

| Method                                         | Where Used                                                                                                                                                                                                                                                                                  |
| :--------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **RAG (Retrieval-Augmented Generation)** | Spec sheets + meeting transcripts loaded into LLM context before synthesis                                                                                                                                                                                                                  |
| **Zero-Shot Prompting**                  | Role-specific summaries and tiered vendor redaction                                                                                                                                                                                                                                         |
| **3D Weighting Matrix**                  | `Role x Topic x Project Phase` priority scoring                                                                                                                                                                                                                                           |
| **Thread Aggregation**                   | `collections.defaultdict` groups messages by `thread_id`                                                                                                                                                                                                                                |
| **Density Scoring**                      | Thread message count adds a bonus score ("heat" detection)                                                                                                                                                                                                                                  |
| **LLM Topic Classification**             | Llama3 semantically classifies each message into canonical topics                                                                                                                                                                                                                           |
| **Noise Filtering**                      | Off-Topic, Platform/IT, HR/Admin, Access Management messages score 0 and are routed to a separate filtered panel — never pollute the digest. Machine-Generated telemetry (CI/CD bots, thermal chamber alerts) is suppressed unless a status transition is detected (e.g.,`PASS → FAIL`) |
| **Async Inference Pattern**              | Digest generation is structured asynchronously (modeled after high-concurrency LLM benchmarking suites) to prevent the Slack ingest pipeline from blocking the user-facing dashboard                                                                                                        |
| **Tiered Access Control**                | 2-tier privacy: Internal (full) vs. Vendor (component-scoped)                                                                                                                                                                                                                               |
| **Process Trigger Detection**            | Keyword + density heuristics flags Sprint or Design Review                                                                                                                                                                                                                                  |
| **Vendor Access Monitoring**             | `Vendor_Access_Status.json` tracks Slack Connect health, last-seen timestamps, and fallback contacts per vendor                                                                                                                                                                           |

### Production Stack (see `EverCurrent_Scaling_Pseudo.md`)

| Layer               | Tool                                                                                                                                                               |
| :------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Identity            | Okta / Active Directory + PLM (Arena / Windchill) — role and part ownership resolved from both HR directory and PLM system                                        |
| Vector DB           | Pinecone / ChromaDB                                                                                                                                                |
| Stream Processing   | Kafka / RabbitMQ                                                                                                                                                   |
| Task Queue          | Celery + Redis                                                                                                                                                     |
| LLM Inference       | vLLM on private GPU cluster                                                                                                                                        |
| Physics/CAD Context | Text-based spec summaries (prototype) → Multi-modal embeddings of 2D drawings and 3D STEP files via Vision-LLMs to semantically "see" design changes (production) |
| Guardrails          | NeMo Guardrails / Guardrails AI                                                                                                                                    |

---

## Project Structure

```
Assignments/
├── app.py                          # Main Streamlit dashboard (all logic)
├── generate_enterprise_data.py     # Generates enterprise_logic.json (mock data + weights)
├── enterprise_logic.json           # Auto-generated: Projects, Weights, Messages
├── users.json                      # User Identity Layer (roles, projects, stakeholders)
├── Vendor_Access_Status.json       # Slack Connect health per vendor (status, last-seen, fallback)
├── Technical_Knowledge_Base/       # Source-of-Truth silo (Specs & Policies)
│   ├── B800_Battery_Spec.txt
│   ├── A1_Actuator_Spec.txt
│   └── Finance_Policy.txt
├── Meeting_Transcripts/            # Non-Slack communication silo
│   └── B800_Thermal_Sync_April29.txt
├── EverCurrent_Design_Overview.md  # Architecture & 3D Scoring design doc
├── EverCurrent_Scaling_Pseudo.md   # Production scaling blueprints
└── venv/                           # Python virtual environment
```

---

## The Scoring Model

```
Thread Score = max(Role_Weight[Role][Topic][Phase]) + (Message_Count * 0.5)
```

- **Role Weight:** Importance of a topic to a specific engineering role.
- **Phase Multiplier:** Embedded in the 3D matrix — same topic, different weight per project stage.
- **Density Bonus:** More messages in a thread = more "heat" = higher priority.

---

## Demo Personas

| Username              | Department       | Role                | Projects          | Access Tier               |
| :-------------------- | :--------------- | :------------------ | :---------------- | :------------------------ |
| `akshay_data`       | Engineering      | Data Engineer       | All 3             | Internal (Full)           |
| `alex_meche`        | Engineering      | Mechanical Engineer | Battery, Chassis  | Internal (Full)           |
| `sarah_ee`          | Engineering      | Electrical Engineer | Battery, Actuator | Internal (Full)           |
| `mike_robotics`     | Engineering      | Robotics Engineer   | Actuator, Chassis | Internal (Full)           |
| `priya_qa`          | Quality          | QA Engineer         | Battery, Actuator | Internal (Full)           |
| `jason_supply`      | Supply Chain     | Supply Chain        | All 3             | Internal (Full)           |
| `lisa_pm`           | Project Mgmt     | Project Manager     | All 3             | Internal (Full)           |
| `finance_mgr`       | Finance          | Finance             | All 3             | Internal + Finance Policy |
| `marketing_lead`    | Marketing        | Marketing           | Chassis only      | Internal (Full)           |
| `taiwan_vendor`     | External Partner | Vendor              | Battery only      | Vendor (Component-Scoped) |
| `harmonic_drive_ag` | External Partner | Vendor              | Actuator only     | Vendor (Component-Scoped) |
| `apex_fabrication`  | External Partner | Vendor              | Chassis only      | Vendor (Component-Scoped) |

---

**Author:** Akshay | **Assignment:** EverCurrent Take-Home
