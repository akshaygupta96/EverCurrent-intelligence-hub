import streamlit as st
import json
import requests
import os
from collections import defaultdict

# --- PATHS ---
KNOWLEDGE_BASE = "Technical_Knowledge_Base"
TRANSCRIPT_BASE = "Meeting_Transcripts"
DATA_PATH = "enterprise_logic.json"
USER_PATH = "users.json"

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
def load_data(path):
    with open(path, "r") as f:
        return json.load(f)

# ─────────────────────────────────────────────
# FIX 1: LLM-BASED TOPIC CLASSIFICATION
# Replaces fragile keyword matching
# ─────────────────────────────────────────────
def classify_topic_with_llm(text):
    """Uses Llama3 to classify a message into a canonical topic or noise category."""
    # First check if it already has a noise_type tag (from mock data)
    prompt = f"""
    You are classifying a Slack message into exactly ONE category.

    Engineering topics: CAD/Design, Thermal, Actuator/Joints, Logistics, PM/Status, Quality, General
    Noise categories: Off-Topic, Platform/IT, HR/Admin, Access Management

    Rules:
    - Use a noise category if the message is NOT about project work (e.g. social chat, Slack outages, HR reminders, vendor access problems)
    - Use an engineering topic if it IS about project work

    Message: "{text}"

    Reply with ONLY the category name. Nothing else.
    """
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": False},
            timeout=20
        )
        raw = response.json().get('response', 'General').strip()
        valid = ["CAD/Design", "Thermal", "Actuator/Joints", "Logistics",
                 "PM/Status", "Quality", "General",
                 "Off-Topic", "Platform/IT", "HR/Admin", "Access Management"]
        for v in valid:
            if v.lower() in raw.lower():
                return v
        return "General"
    except:
        return "General"

# ─────────────────────────────────────────────
# FIX 2: THREAD AGGREGATION
# Groups messages by thread_id before scoring
# ─────────────────────────────────────────────
def aggregate_threads(messages):
    """Groups messages into threads. Parent message is key."""
    threads = defaultdict(list)
    for msg in messages:
        t_id = msg['thread_id'] if msg['thread_id'] else msg['id']
        threads[t_id].append(msg)
    return threads

# ─────────────────────────────────────────────
# PRIVACY & KNOWLEDGE RETRIEVAL
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
# TIERED PRIVACY FILTER
# Tier 1 - Internal:  Full access (specs, meetings, finance policy)
# Tier 2 - Vendor:    Component-relevant specs only. No internal
#                     decisions, no financial docs, no other vendors.
# ─────────────────────────────────────────────────────────────
def load_ground_truth(project_name, user_profile):
    """Retrieves ground truth docs based on access tier."""
    context = ""
    department = user_profile.get('department', '')
    is_vendor = department == "External Partner"

    # --- TIER 1 & 2: Technical Spec (both get this, but vendors get a note) ---
    spec_file = None
    if "Battery" in project_name:
        spec_file = os.path.join(KNOWLEDGE_BASE, "B800_Battery_Spec.txt")
    elif "Actuator" in project_name:
        spec_file = os.path.join(KNOWLEDGE_BASE, "A1_Actuator_Spec.txt")

    if spec_file and os.path.exists(spec_file):
        with open(spec_file, "r") as f:
            spec_content = f.read()
        if is_vendor:
            # Vendors get the component-level specs relevant to their parts
            # but NOT system-level architecture details
            context += f"--- COMPONENT SPEC (Relevant to your parts) ---\n{spec_content}\n"
            context += "[NOTE: System-level architecture and integration details are confidential.]\n"
        else:
            context += f"--- TECHNICAL SPEC ---\n{spec_content}\n"

    # --- TIER 1 ONLY: Internal silos ---
    if not is_vendor:
        # Meeting transcripts — now covering all 3 projects
        transcript_map = {
            "Battery B-800": "B800_Thermal_Sync_April29.txt",
            "Actuator A-1":  "A1_Actuator_Kickoff_April22.txt",
            "Chassis C-200": "C200_Chassis_Kickoff_April15.txt"
        }
        if project_name in transcript_map:
            p = os.path.join(TRANSCRIPT_BASE, transcript_map[project_name])
            if os.path.exists(p):
                with open(p, "r") as f:
                    context += f"--- RECENT MEETING DECISIONS ---\n{f.read()}\n"

        # Finance: policy doc + Q2 budget (Finance and Project Manager)
        if user_profile.get('department') in ["Finance", "Project Management"]:
            p = os.path.join(KNOWLEDGE_BASE, "Finance_Policy.txt")
            if os.path.exists(p):
                with open(p, "r") as f:
                    context += f"--- FINANCE POLICY ---\n{f.read()}\n"
            p = os.path.join(KNOWLEDGE_BASE, "Q2_Hardware_Budget.txt")
            if os.path.exists(p):
                with open(p, "r") as f:
                    context += f"--- Q2 HARDWARE BUDGET ---\n{f.read()}\n"
    else:
        context += "\n[ACCESS RESTRICTED: Internal meeting logs, financial data, and cross-vendor information are not accessible to external partners.]\n"

    return context if context else "No ground truth documents found."

# ─────────────────────────────────────────────
# AI SYNTHESIS
# ─────────────────────────────────────────────
def get_ollama_summary(thread_text, user_profile, project_phase, context):
    department = user_profile.get('department', 'Engineering')
    is_vendor = department == "External Partner"

    if is_vendor:
        safety_protocol = (
            "This user is an EXTERNAL PARTNER / COMPONENT SUPPLIER. "
            "You MAY reference engineering specs that are directly relevant to their supplied parts. "
            "You MUST NOT mention: internal cost figures, CM penalty clauses, "
            "proprietary mitigation strategies (e.g. specific material names chosen internally), "
            "other vendor names or pricing, or any internal meeting decisions. "
            "Focus on: component interface requirements, delivery schedule impact, "
            "and what specification data they need to fulfill their order."
        )
    else:
        safety_protocol = (
            "This is an internal EverCurrent employee. "
            "Provide full technical synthesis. Flag spec violations explicitly. "
            "Reference meeting decisions and policy documents where relevant."
        )

    prompt = f"""
    You are an Engineering Intelligence Agent for EverCurrent, a robotics hardware company.
    EverCurrent designs and manufactures products for external customers.
    This digest tool is for EverCurrent's internal teams and authorized component suppliers.

    USER: {user_profile['username']} | ROLE: {user_profile['role']} | DEPT: {department}
    PROJECT PHASE: {project_phase}

    ACCESS PROTOCOL: {safety_protocol}

    GROUND TRUTH (apply access protocol above):
    {context}

    CONVERSATION:
    {thread_text}

    TASK:
    1. Summarize the key event.
    2. Cross-reference the Ground Truth. Flag violations or relevant past decisions.
    3. If an action item exists for this user's role, state it. Otherwise, state 'No action required.'
    Max 3 sentences.
    """
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": False},
            timeout=60
        )
        return response.json().get('response', '').strip()
    except:
        return "[Offline Mode] AI Agent unavailable. Top thread flagged for manual review."

# ─────────────────────────────────────────────
# FIX 3: PROCESS TRIGGERS
# Analyzes thread density and keywords to recommend formal process actions
# ─────────────────────────────────────────────
def detect_process_triggers(project_threads):
    """Scans all threads for signals that a formal process action is needed."""
    triggers = []
    blocker_keywords = ["blocker", "blocked", "failing", "over spec", "critical", "miss", "delay", "error"]
    review_keywords = ["design review", "urgent", "interfere", "violated"]
    total_messages = sum(len(t) for t in project_threads.values())

    # Sprint Trigger: high message volume in 24h = team is overwhelmed
    if total_messages >= 6:
        triggers.append(("🚨 Sprint Recommended", "High message volume detected. Consider scheduling a sprint to resolve open blockers."))

    for t_id, messages in project_threads.items():
        all_text = " ".join(m['text'].lower() for m in messages)
        # Design Review Trigger
        if any(k in all_text for k in blocker_keywords) and len(messages) >= 2:
            triggers.append(("📋 Design Review Recommended", f"Thread has {len(messages)} messages with blocker-level language detected."))
            break
        if any(k in all_text for k in review_keywords):
            triggers.append(("📋 Design Review Recommended", "Conflicting technical signals detected in an active thread."))
            break

    return list({t[0]: t for t in triggers}.values())  # dedupe by title

# ─────────────────────────────────────────────
# DESIGN DEBT TRIGGER
# Flags hardware workaround language that requires a formal ECO
# before the design is frozen for DVT/PVT
# ─────────────────────────────────────────────
DESIGN_DEBT_KEYWORDS = [
    "shim", "zip-tie", "zip tie", "hot-fix", "hotfix",
    "workaround", "temporary", "tape", "jury-rig",
    "duct tape", "band-aid", "bandaid", "quick fix", "kludge"
]

def detect_design_debt(threads):
    """Scans thread text for hardware workaround language.
    Returns a list of (thread_snippet, matched_keyword) tuples.
    """
    debt_alerts = []
    for t_id, messages in threads.items():
        for msg in messages:
            text_lower = msg['text'].lower()
            for keyword in DESIGN_DEBT_KEYWORDS:
                if keyword in text_lower:
                    debt_alerts.append({
                        "keyword": keyword,
                        "user": msg.get('user', 'unknown'),
                        "channel": msg.get('channel', 'unknown'),
                        "snippet": msg['text']
                    })
                    break  # one alert per message is enough
    return debt_alerts

# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────
st.set_page_config(page_title="EverCurrent Intelligence Hub", layout="wide")
st.title("EverCurrent Engineering Intelligence Hub")
st.markdown("---")

ent_data = load_data(DATA_PATH)
users_data = load_data(USER_PATH)

# Build identity lookup: username -> {display_name, role} from users.json
# This is the core of the Identity Source of Truth — role is NEVER inferred from the username string
identity_map = {
    u['username']: {
        "display_name": u.get('display_name', u['username']),
        "role": u.get('role', 'Unknown')
    }
    for u in users_data['users']
}

# Sidebar
st.sidebar.header("User Identity")

# Show display names for login — role is resolved from users.json, not the username
name_map = {u['username']: u.get('display_name', u['username']) for u in users_data['users']}
current_user_name = st.sidebar.selectbox(
    "Select User",
    [u['username'] for u in users_data['users']],
    format_func=lambda x: name_map[x]   # Shows "Alex Johnson" not "alex.johnson"
)
current_user = next(u for u in users_data['users'] if u['username'] == current_user_name)

st.sidebar.caption(f"Slack handle: `{current_user['username']}`")
st.sidebar.caption(f"Role (from Identity Store): **{current_user['role']}** | {current_user['department']}")

if current_user.get('department') == "External Partner":
    st.sidebar.warning("⚠️ EXTERNAL PARTNER SESSION — Privacy filters active.")
else:
    st.sidebar.success(f"✅ INTERNAL — {current_user['role']}")

st.sidebar.caption(f"Stakeholders: {', '.join(current_user.get('stakeholders', []))}")

if st.sidebar.button("Generate My Briefing"):
    st.header(f"Personalized Briefing: {current_user['username']}")

    for project_name in current_user['assigned_projects']:
        proj_info = ent_data['projects'].get(project_name)
        current_phase = proj_info['phase']

        st.subheader(f"📂 {project_name}  |  `{current_phase}`")

        # Filter messages for this project
        project_msgs = [m for m in ent_data['messages'] if m['project'] == project_name]

        # FIX 2: Aggregate into threads
        threads = aggregate_threads(project_msgs)

        # FIX 3: Detect process triggers BEFORE scoring (Internal only)
        if current_user.get('department') != "External Partner":
            triggers = detect_process_triggers(threads)
            if triggers:
                for label, reason in triggers:
                    st.warning(f"**{label}:** {reason}")

            # Design Debt Detection
            debt_alerts = detect_design_debt(threads)
            if debt_alerts:
                for alert in debt_alerts:
                    st.error(
                        f"⚠️ **Design Debt Alert** — Workaround language detected "
                        f"(`\"{alert['keyword']}\"`) in `#{alert['channel']}` by `{alert['user']}`.\n\n"
                        f"*\"{alert['snippet']}\"*\n\n"
                        f"**Action Required:** Log an Engineering Change Order (ECO) before design freeze."
                    )

        # Score threads — split into digest vs noise buckets
        scored_threads = []
        filtered_noise = []   # Off-Topic, Platform/IT, HR/Admin, Access Management

        for t_id, messages in threads.items():
            thread_content = ""
            max_score = 0
            topics = set()
            channels = set()
            noise_types = set()

            for msg in messages:
                channels.add(msg.get('channel', 'unknown'))
                thread_content += f"[{msg.get('channel','?')}] {msg['user']}: {msg['text']}\n"

                # Use pre-tagged noise_type if present, else classify with LLM
                if 'noise_type' in msg:
                    topic = msg['noise_type']
                else:
                    topic = classify_topic_with_llm(msg['text'])

                topics.add(topic)
                score = ent_data['weights'].get(current_user['role'], {}).get(topic, {}).get(current_phase, 0)
                max_score = max(max_score, score)

                if topic in ["Off-Topic", "Platform/IT", "HR/Admin", "Access Management"]:
                    noise_types.add(topic)

            final_score = max_score + (len(messages) * 0.5)

            thread_obj = {
                "content": thread_content,
                "topic": list(topics)[0],
                "score": final_score,
                "count": len(messages),
                "channels": ", ".join(channels)
            }

            # Route to noise bucket if ALL messages in thread are noise
            if noise_types and max_score == 0:
                filtered_noise.append(thread_obj)
            else:
                scored_threads.append(thread_obj)

        ranked = sorted(scored_threads, key=lambda x: x['score'], reverse=True)

        # Load ground truth for this user/project intersection
        context = load_ground_truth(project_name, current_user)

        # Display top threads
        for item in ranked[:2]:
            with st.container():
                col1, col2 = st.columns([1, 5])
                with col1:
                    st.metric("Priority", f"{item['score']:.1f}")
                    st.caption(f"{item['count']} msgs")
                    st.caption(f"`{item['topic']}`")
                with col2:
                    # SHOW SLACK CHAT VISIBLY BY DEFAULT
                    st.markdown(f"**Channels:** `{item['channels']}`")
                    st.markdown("**Slack Thread:**")
                    for line in item['content'].strip().split("\n"):
                        if line.strip():
                            parts = line.split("] ", 1)
                            channel_tag = parts[0].replace("[", "") if len(parts) > 1 else ""
                            msg_body = parts[1] if len(parts) > 1 else line
                            user_part = msg_body.split(": ", 1)
                            sender = user_part[0] if len(user_part) > 1 else "?"
                            text = user_part[1] if len(user_part) > 1 else msg_body
                            # Look up display name and role from Identity Store
                            identity = identity_map.get(sender, {"display_name": sender, "role": "Unknown"})
                            display = identity["display_name"]
                            role_tag = identity["role"]
                            st.markdown(f"> `#{channel_tag}` **{display}** *({role_tag})*: {text}")
                    st.markdown("")
                    with st.spinner("Agent cross-referencing silos..."):
                        summary = get_ollama_summary(item['content'], current_user, current_phase, context)
                        st.success(f"**AI Agent Summary:** {summary}")
            st.markdown("---")

        with st.expander("Show loaded knowledge silos (Ground Truth)"):
            st.code(context)

        # NOISE PANEL: Show what was filtered out
        if filtered_noise:
            noise_labels = {"Off-Topic": "💬", "Platform/IT": "🖥️",
                            "HR/Admin": "📋", "Access Management": "🔐"}
            with st.expander(f"🚫 Filtered Noise ({len(filtered_noise)} threads excluded from digest)"):
                for item in filtered_noise:
                    icon = noise_labels.get(item['topic'], "🔇")
                    st.markdown(f"{icon} **`{item['topic']}`** — `{item['channels']}`")
                    for line in item['content'].strip().split("\n"):
                        if line.strip():
                            parts = line.split("] ", 1)
                            channel_tag = parts[0].replace("[", "") if len(parts) > 1 else ""
                            msg_body = parts[1] if len(parts) > 1 else line
                            user_part = msg_body.split(": ", 1)
                            sender = user_part[0] if len(user_part) > 1 else "?"
                            text = user_part[1] if len(user_part) > 1 else msg_body
                            identity = identity_map.get(sender, {"display_name": sender, "role": "Unknown"})
                            display = identity["display_name"]
                            role_tag = identity["role"]
                            st.markdown(f"> `#{channel_tag}` **{display}** *({role_tag})*: {text}")
                    st.markdown("")

    # VENDOR ACCESS ALERTS (shown once at the bottom, internal users only)
    if current_user.get('department') != "External Partner":
        try:
            vendor_status = load_data("Vendor_Access_Status.json")
            degraded = [v for v in vendor_status['vendor_channels']
                        if v['status'] == 'degraded' and
                        any(p in current_user['assigned_projects'] for p in [v['project']])]
            if degraded:
                st.markdown("---")
                st.subheader("🔐 Vendor Access Alerts")
                for v in degraded:
                    st.error(
                        f"**{v['vendor']}** ({v['project']}) — "
                        f"Slack Connect status: `{v['invite_status']}` | "
                        f"Last seen: `{v['last_message_ts']}` | "
                        f"Fallback: `{v['fallback_email']}` \n\n"
                        f"⚠️ {v['alert']}"
                    )
        except:
            pass

else:
    st.info("Select a persona from the sidebar and generate your personalized briefing.")
