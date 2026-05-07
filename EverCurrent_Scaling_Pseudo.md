## Overview

This document describes the **production-grade architecture** that replaces the prototype's
flat JSON files and local Ollama calls. The core reasoning logic (3D matrix, RAG, noise filtering)
stays identical — only the infrastructure connectors change.

### The Prototype Architecture (Protoype)

```text
┌─────────────────────────────────────────────────────────┐
│           EverCurrent Prototype (Local Dev)             │
│                                                         │
│   [Local Files]        [Local Logic]      [Local AI]    │
│   - users.json          - app.py           - Ollama     │
│   - enterprise_logic.json - 3D Matrix      - Llama 3 8B │
│   - Text Silos          - State Mgmt                    │
│         │                    │                  │       │
│         └──────────┬─────────┴────────┬─────────┘       │
│                    │                  │                 │
│             [Context Loading]  [Topic Classification]   │
│                    │                  │                 │
│                    └─────────┬────────┘                 │
│                              │                          │
│                   [Streamlit UI Dashboard]              │
│                   - Personalized Briefing               │
│                   - Live Simulation Controls            │
└─────────────────────────────────────────────────────────┘
```

---

## 1. The Data Privacy & Redaction Layer

Handles External Partners (Slack Connect) and ensures IP never leaks.

*Note: While the prototype uses application-level RBAC (shown below), production scale (based on Gruve architecture) implements **Network and Identity-level segmentation** where internal Vector DBs reside in a secured VPC, completely unreachable by Vendor LLM agents via IAM constraints.*

```python
class SecurityFilter:
    def preprocess(self, data, recipient_profile):
        """
        Scans data for Internal-only patterns and redacts
        them if the recipient is an External Partner.
        """
        if recipient_profile.is_external:
            # 1. Strip internal links, hostnames, internal repo URLs
            data = Redact.links(data, internal_domain="evercurrent.com")

            # 2. Sensitivity scan via secondary LLM or regex ruleset
            if SensitivityAgent.is_high_risk(data):
                return "[REDACTED: Proprietary Design Detail]"

        return data

    def authorize_silo_access(self, user, silo_id):
        """RBAC: Role-Based Access Control per silo."""
        silo_permissions = {
            "Finance_Policy":       ["Finance", "Project Manager"],
            "Meeting_Transcripts":  ["Engineering", "Quality", "Project Manager"],
            "Technical_Spec":       ["Engineering", "Quality", "Vendor"],  # Vendors: component scope only
        }
        allowed_roles = silo_permissions.get(silo_id, [])
        if user.role not in allowed_roles:
            raise AccessDenied(f"{user.role} cannot access silo: {silo_id}")
```

---

## 2. The Ingestion Pipeline

Replaces flat JSON files with real-time event streams.

```python
class DataIngestor:
    def on_slack_message(self, message_event):
        """Processes real-time Slack streams via Webhooks."""
        # 1. Resolve identity from Slack user_id → role via Okta SCIM
        user_profile = IdentityService.resolve(message_event.user_id)

        # 2. Scrub PII
        clean_text = SecurityFilter.scrub(message_event.text)

        # 3. Classify topic (LLM call, async)
        topic = TopicClassifier.classify(clean_text)

        # 4. Route noise away immediately — never enters the digest pipeline
        if topic in ["Off-Topic", "Platform/IT", "HR/Admin"]:
            NoiseLog.append(clean_text, topic)
            if topic == "Access Management":
                VendorAccessMonitor.flag(message_event.channel)
            return

        # 5. Index into Vector DB for semantic retrieval
        VectorDB.index(
            text=clean_text,
            metadata={
                "source": "slack",
                "user": user_profile.username,
                "role": user_profile.role,
                "project": ProjectMapper.infer(message_event.channel),
                "thread_id": message_event.thread_ts,
                "timestamp": message_event.ts
            }
        )

    def on_meeting_completed(self, transcript):
        """Ingests Zoom/Otter transcripts after meeting ends."""
        decisions = LLM.extract_decisions(transcript)
        VectorDB.index(
            text=decisions,
            metadata={"source": "meeting", "type": "decision", "visibility": "internal"}
        )

    def on_spec_sheet_updated(self, file_event):
        """Triggered when a new spec is uploaded to PLM/Drive."""
        text = PDFParser.extract(file_event.file_path)
        VectorDB.index(
            text=text,
            metadata={"source": "spec_sheet", "project": file_event.project, "visibility": "internal"}
        )
```

---

## 3. The Contextual Retrieval Engine (RAG)

Replaces loading flat `.txt` files with semantic search across the Vector DB.

```python
def retrieve_ground_truth(query_context, user_profile, project_id):
    """
    Finds the intersection of truth across Engineering, Finance, and Logistics silos.
    Applies access control before returning any content.
    """
    results = {}

    # 1. Technical specs for this project (vendors get component scope only)
    spec_filter = {"source": "spec_sheet", "project": project_id}
    results["technical"] = VectorDB.query(text=query_context, filter=spec_filter, top_k=3)

    # 2. Recent meeting decisions (internal only)
    if not user_profile.is_external:
        meeting_filter = {"source": "meeting", "type": "decision", "project": project_id}
        results["decisions"] = VectorDB.query(text=query_context, filter=meeting_filter, top_k=2)

    # 3. Finance policy (Finance + PM only)
    if user_profile.role in ["Finance", "Project Manager"]:
        policy_filter = {"source": "finance_policy"}
        results["policy"] = VectorDB.query(text=query_context, filter=policy_filter, top_k=1)

    return results
```

---

## 4. The Multi-Project Orchestrator

Generates a cross-project portfolio digest for any user.

```python
def generate_portfolio_digest(user_id):
    # 1. Resolve full identity from Okta SCIM
    user = IdentityService.get_profile(user_id)
    global_digest = []

    for project in user.assigned_projects:
        # 2. Get live project phase from PLM registry
        current_phase = ProjectRegistry.get_phase(project.id)

        # 3. Fetch and aggregate hot threads from last 24h
        hot_threads = VectorDB.get_recent_clusters(
            project_id=project.id,
            hours=24,
            min_messages=2
        )

        for thread in hot_threads:
            # 4. 3D Matrix scoring: Role × Topic × Phase
            score = ScoringEngine.calculate(
                topics=thread.topics,
                user_role=user.role,
                project_phase=current_phase,
                message_count=thread.count  # density bonus
            )

            # 5. RAG-grounded AI synthesis with access-controlled context
            context = retrieve_ground_truth(thread.content, user, project.id)
            impact = LLM.interpret(
                content=thread.content,
                target_role=user.role,
                ground_truth=context,
                safety_protocol=SecurityFilter.get_protocol(user)
            )

            global_digest.append({
                "project": project.name,
                "phase": current_phase,
                "impact": impact,
                "score": score
            })

    # 6. Sort globally across all projects by score
    return sorted(global_digest, key=lambda x: x['score'], reverse=True)
```

---

## 5. Production Deployment Architecture

```text
┌─────────────────────────────────────────────────────────┐
│            EverCurrent Intelligence Hub (Scale)         │
│                                                         │
│   [Slack Webhooks]  [Zoom/Otter]  [PLM/Windchill]       │
│         │               │              │                │
│         └───────────────┴──────────────┘                │
│                         │                               │
│           [Async Ingestion API (FastAPI)]               │
│           [SecurityFilter & Metadata Tagging]           │
│                         │                               │
│             [Redis Queue / Celery Workers]              │
│                         │                               │
│       ┌─────────────────┴─────────────────┐             │
│       │                                   │             │
│  [INTERNAL VPC]                    [EXTERNAL VPC]       │
│  - Internal Vector DB              - Vendor Vector DB   │
│  - IP/Budgets/Transcripts          - Public Specs/Logs  │
│  - Internal LLM Agent              - Vendor LLM Agent   │
│       │                                   │             │
│       └─────────────────┬─────────────────┘             │
│                         │                               │
│  [Identity]             │           [Inference]         │
│  Okta SCIM Resolver ────┘────────── vLLM GPU Cluster    │
│                                                         │
│               [Portfolio Digest API]                    │
│                         │                               │
│           [React / Next.js Enterprise Hub]              │
│           (Highly-performant, RBAC-enabled UI)          │
└─────────────────────────────────────────────────────────┘
```

### The Transition Strategy (Prototype → Production)

1. **Frontend:** Migrate from **Streamlit** (Rapid Prototyping) to **React/Next.js**. This enables sub-second UI interactions, custom branding, and granular component-level access control.
2. **Security:** Implement **VPC-level isolation**. Instead of just code-level "if" statements, the Vendor LLM Agent physically lacks the network routing or IAM permissions to reach the Internal VPC.
3. **Storage:** Transition from **JSON files** to **Vector Databases (Pinecone/Milvus)** with auto-syncing ETL pipelines from PLM systems (Windchill).
4. **Inference:** Move from local **Ollama** to a distributed **vLLM GPU Cluster** to support thousands of concurrent briefings.
