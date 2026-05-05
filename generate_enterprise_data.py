import json

# --- THE PROJECT REGISTRY ---
projects = {
    "Battery B-800": {
        "phase": "DVT (Design Validation)",
        "priority_level": "Critical",
        "specs": "B800_Battery_Spec.txt",
        "lead_engineer": "alex_meche",
        "description": "High-voltage lithium-ion battery module for robotics platform."
    },
    "Actuator A-1": {
        "phase": "EVT (Prototyping)",
        "priority_level": "Medium",
        "specs": "A1_Actuator_Spec.txt",
        "lead_engineer": "mike_robotics",
        "description": "Robotic arm elbow joint actuator with harmonic drive gearbox."
    },
    "Chassis C-200": {
        "phase": "Concept",
        "priority_level": "Low",
        "specs": None,
        "lead_engineer": "alex_meche",
        "description": "Next-gen lightweight aluminum chassis for the field robot platform."
    }
}

# --- THE 3D WEIGHTING MATRIX: Role x Topic x Phase ---
complex_weights = {
    "Mechanical Engineer": {
        "CAD/Design":      {"Concept": 10, "EVT (Prototyping)": 10, "DVT (Design Validation)": 9,  "PVT (Production)": 2},
        "Thermal":         {"Concept": 5,  "EVT (Prototyping)": 8,  "DVT (Design Validation)": 10, "PVT (Production)": 3},
        "Actuator/Joints": {"Concept": 6,  "EVT (Prototyping)": 9,  "DVT (Design Validation)": 7,  "PVT (Production)": 2},
        "Logistics":       {"Concept": 1,  "EVT (Prototyping)": 2,  "DVT (Design Validation)": 5,  "PVT (Production)": 7},
        "PM/Status":       {"Concept": 3,  "EVT (Prototyping)": 4,  "DVT (Design Validation)": 6,  "PVT (Production)": 5},
        "Quality":         {"Concept": 2,  "EVT (Prototyping)": 4,  "DVT (Design Validation)": 8,  "PVT (Production)": 9}
    },
    "Electrical Engineer": {
        "CAD/Design":      {"Concept": 6,  "EVT (Prototyping)": 7,  "DVT (Design Validation)": 8,  "PVT (Production)": 2},
        "Thermal":         {"Concept": 5,  "EVT (Prototyping)": 7,  "DVT (Design Validation)": 10, "PVT (Production)": 4},
        "Actuator/Joints": {"Concept": 4,  "EVT (Prototyping)": 6,  "DVT (Design Validation)": 5,  "PVT (Production)": 2},
        "Logistics":       {"Concept": 1,  "EVT (Prototyping)": 3,  "DVT (Design Validation)": 5,  "PVT (Production)": 6},
        "PM/Status":       {"Concept": 3,  "EVT (Prototyping)": 4,  "DVT (Design Validation)": 5,  "PVT (Production)": 5},
        "Quality":         {"Concept": 3,  "EVT (Prototyping)": 5,  "DVT (Design Validation)": 9,  "PVT (Production)": 10}
    },
    "Thermal Engineer": {
        "CAD/Design":      {"Concept": 6,  "EVT (Prototyping)": 8,  "DVT (Design Validation)": 8,  "PVT (Production)": 4},
        "Thermal":         {"Concept": 10, "EVT (Prototyping)": 10, "DVT (Design Validation)": 10, "PVT (Production)": 8},
        "Actuator/Joints": {"Concept": 4,  "EVT (Prototyping)": 6,  "DVT (Design Validation)": 5,  "PVT (Production)": 2},
        "Logistics":       {"Concept": 1,  "EVT (Prototyping)": 2,  "DVT (Design Validation)": 4,  "PVT (Production)": 5},
        "PM/Status":       {"Concept": 2,  "EVT (Prototyping)": 4,  "DVT (Design Validation)": 5,  "PVT (Production)": 5},
        "Quality":         {"Concept": 3,  "EVT (Prototyping)": 5,  "DVT (Design Validation)": 8,  "PVT (Production)": 7}
    },
    "Robotics Engineer": {
        "CAD/Design":      {"Concept": 7,  "EVT (Prototyping)": 8,  "DVT (Design Validation)": 6,  "PVT (Production)": 2},
        "Thermal":         {"Concept": 3,  "EVT (Prototyping)": 5,  "DVT (Design Validation)": 7,  "PVT (Production)": 3},
        "Actuator/Joints": {"Concept": 9,  "EVT (Prototyping)": 10, "DVT (Design Validation)": 9,  "PVT (Production)": 4},
        "Logistics":       {"Concept": 1,  "EVT (Prototyping)": 2,  "DVT (Design Validation)": 4,  "PVT (Production)": 6},
        "PM/Status":       {"Concept": 3,  "EVT (Prototyping)": 5,  "DVT (Design Validation)": 6,  "PVT (Production)": 6},
        "Quality":         {"Concept": 2,  "EVT (Prototyping)": 4,  "DVT (Design Validation)": 8,  "PVT (Production)": 9}
    },
    "Supply Chain": {
        "CAD/Design":      {"Concept": 3,  "EVT (Prototyping)": 3,  "DVT (Design Validation)": 4,  "PVT (Production)": 2},
        "Thermal":         {"Concept": 1,  "EVT (Prototyping)": 2,  "DVT (Design Validation)": 4,  "PVT (Production)": 3},
        "Actuator/Joints": {"Concept": 2,  "EVT (Prototyping)": 2,  "DVT (Design Validation)": 3,  "PVT (Production)": 2},
        "Logistics":       {"Concept": 6,  "EVT (Prototyping)": 8,  "DVT (Design Validation)": 9,  "PVT (Production)": 10},
        "PM/Status":       {"Concept": 5,  "EVT (Prototyping)": 6,  "DVT (Design Validation)": 8,  "PVT (Production)": 9},
        "Quality":         {"Concept": 2,  "EVT (Prototyping)": 3,  "DVT (Design Validation)": 5,  "PVT (Production)": 7}
    },
    "Project Manager": {
        "CAD/Design":      {"Concept": 5,  "EVT (Prototyping)": 5,  "DVT (Design Validation)": 7,  "PVT (Production)": 3},
        "Thermal":         {"Concept": 3,  "EVT (Prototyping)": 5,  "DVT (Design Validation)": 9,  "PVT (Production)": 4},
        "Actuator/Joints": {"Concept": 4,  "EVT (Prototyping)": 6,  "DVT (Design Validation)": 7,  "PVT (Production)": 3},
        "Logistics":       {"Concept": 5,  "EVT (Prototyping)": 6,  "DVT (Design Validation)": 8,  "PVT (Production)": 9},
        "PM/Status":       {"Concept": 8,  "EVT (Prototyping)": 9,  "DVT (Design Validation)": 10, "PVT (Production)": 10},
        "Quality":         {"Concept": 3,  "EVT (Prototyping)": 5,  "DVT (Design Validation)": 8,  "PVT (Production)": 9}
    },
    "Finance": {
        "CAD/Design":      {"Concept": 2,  "EVT (Prototyping)": 2,  "DVT (Design Validation)": 2,  "PVT (Production)": 1},
        "Thermal":         {"Concept": 1,  "EVT (Prototyping)": 2,  "DVT (Design Validation)": 4,  "PVT (Production)": 2},
        "Actuator/Joints": {"Concept": 1,  "EVT (Prototyping)": 2,  "DVT (Design Validation)": 2,  "PVT (Production)": 1},
        "Logistics":       {"Concept": 4,  "EVT (Prototyping)": 5,  "DVT (Design Validation)": 7,  "PVT (Production)": 10},
        "PM/Status":       {"Concept": 5,  "EVT (Prototyping)": 5,  "DVT (Design Validation)": 7,  "PVT (Production)": 9},
        "Quality":         {"Concept": 2,  "EVT (Prototyping)": 3,  "DVT (Design Validation)": 5,  "PVT (Production)": 8}
    },
    "QA Engineer": {
        "CAD/Design":      {"Concept": 3,  "EVT (Prototyping)": 4,  "DVT (Design Validation)": 6,  "PVT (Production)": 4},
        "Thermal":         {"Concept": 3,  "EVT (Prototyping)": 5,  "DVT (Design Validation)": 9,  "PVT (Production)": 7},
        "Actuator/Joints": {"Concept": 3,  "EVT (Prototyping)": 5,  "DVT (Design Validation)": 8,  "PVT (Production)": 6},
        "Logistics":       {"Concept": 2,  "EVT (Prototyping)": 3,  "DVT (Design Validation)": 4,  "PVT (Production)": 5},
        "PM/Status":       {"Concept": 3,  "EVT (Prototyping)": 4,  "DVT (Design Validation)": 6,  "PVT (Production)": 6},
        "Quality":         {"Concept": 5,  "EVT (Prototyping)": 7,  "DVT (Design Validation)": 10, "PVT (Production)": 10}
    },
    "Marketing": {
        "CAD/Design":      {"Concept": 2,  "EVT (Prototyping)": 2,  "DVT (Design Validation)": 2,  "PVT (Production)": 1},
        "Thermal":         {"Concept": 1,  "EVT (Prototyping)": 1,  "DVT (Design Validation)": 1,  "PVT (Production)": 1},
        "Actuator/Joints": {"Concept": 1,  "EVT (Prototyping)": 1,  "DVT (Design Validation)": 1,  "PVT (Production)": 1},
        "Logistics":       {"Concept": 3,  "EVT (Prototyping)": 4,  "DVT (Design Validation)": 5,  "PVT (Production)": 8},
        "PM/Status":       {"Concept": 8,  "EVT (Prototyping)": 7,  "DVT (Design Validation)": 7,  "PVT (Production)": 9},
        "Quality":         {"Concept": 2,  "EVT (Prototyping)": 3,  "DVT (Design Validation)": 4,  "PVT (Production)": 7}
    },
    "Data Engineer": {
        "CAD/Design":      {"Concept": 3,  "EVT (Prototyping)": 4,  "DVT (Design Validation)": 4,  "PVT (Production)": 2},
        "Thermal":         {"Concept": 4,  "EVT (Prototyping)": 6,  "DVT (Design Validation)": 8,  "PVT (Production)": 5},
        "Actuator/Joints": {"Concept": 4,  "EVT (Prototyping)": 6,  "DVT (Design Validation)": 6,  "PVT (Production)": 4},
        "Logistics":       {"Concept": 3,  "EVT (Prototyping)": 4,  "DVT (Design Validation)": 5,  "PVT (Production)": 6},
        "PM/Status":       {"Concept": 5,  "EVT (Prototyping)": 6,  "DVT (Design Validation)": 7,  "PVT (Production)": 7},
        "Quality":         {"Concept": 3,  "EVT (Prototyping)": 5,  "DVT (Design Validation)": 7,  "PVT (Production)": 8}
    },
    "Vendor": {
        "CAD/Design":      {"Concept": 1,  "EVT (Prototyping)": 1,  "DVT (Design Validation)": 1,  "PVT (Production)": 1},
        "Thermal":         {"Concept": 1,  "EVT (Prototyping)": 1,  "DVT (Design Validation)": 1,  "PVT (Production)": 1},
        "Actuator/Joints": {"Concept": 1,  "EVT (Prototyping)": 1,  "DVT (Design Validation)": 1,  "PVT (Production)": 1},
        "Logistics":       {"Concept": 7,  "EVT (Prototyping)": 8,  "DVT (Design Validation)": 9,  "PVT (Production)": 10},
        "PM/Status":       {"Concept": 4,  "EVT (Prototyping)": 5,  "DVT (Design Validation)": 7,  "PVT (Production)": 8},
        "Quality":         {"Concept": 2,  "EVT (Prototyping)": 3,  "DVT (Design Validation)": 4,  "PVT (Production)": 6},
        # --- NOISE CATEGORIES: Score 0 across all roles/phases ---
        "Off-Topic":       {"Concept": 0,  "EVT (Prototyping)": 0,  "DVT (Design Validation)": 0,  "PVT (Production)": 0},
        "Platform/IT":     {"Concept": 0,  "EVT (Prototyping)": 0,  "DVT (Design Validation)": 0,  "PVT (Production)": 0},
        "HR/Admin":        {"Concept": 0,  "EVT (Prototyping)": 0,  "DVT (Design Validation)": 0,  "PVT (Production)": 0},
        "Access Management":{"Concept": 0, "EVT (Prototyping)": 0,  "DVT (Design Validation)": 0,  "PVT (Production)": 0}
    }
}

# --- REALISTIC SLACK MESSAGES: 3 Projects, Multiple Channels & Threads ---
mock_messages = [

    # ─────────────────────────────────────────────────────────────
    # PROJECT: Battery B-800 | Phase: DVT (Design Validation)
    # Scenario: A 5mm CAD shift caused a thermal chain reaction
    # ─────────────────────────────────────────────────────────────

    # Thread 1: CAD Change (initiated by alex in #battery-design)
    {
        "id": "b_001", "thread_id": None,
        "project": "Battery B-800", "channel": "battery-design",
        "user": "alex.johnson",
        "text": "Uploaded Rev 3 CAD for the baseplate. Shifted the mounting holes 5mm left to clear the new cable harness. Flagging for review."
    },
    {
        "id": "b_002", "thread_id": "b_001",
        "project": "Battery B-800", "channel": "battery-design",
        "user": "sarah.chen",
        "text": "@alex_meche that 5mm shift might be interfering with the MOSFET thermal pads on the PDB. The clearance spec is only 3mm."
    },
    {
        "id": "b_003", "thread_id": "b_001",
        "project": "Battery B-800", "channel": "battery-design",
        "user": "alex.johnson",
        "text": "Measured it. We are at 0.8mm clearance. You are right, this is outside spec. Looping in Tom."
    },
    {
        "id": "b_004", "thread_id": "b_001",
        "project": "Battery B-800", "channel": "battery-design",
        "user": "priya.kumar",
        "text": "This will need a formal NCR (Non-Conformance Report) before DVT builds start. I will draft it pending thermal confirmation."
    },

    # Thread 2: Thermal Blocker (in #thermal-testing)
    {
        "id": "b_005", "thread_id": None,
        "project": "Battery B-800", "channel": "thermal-testing",
        "user": "tom.harris",
        "text": "DVT thermal sims complete. MOSFETs peaking at 110C under load. Spec limit is 105C. We are 5C over. This is a hard DVT blocker."
    },
    {
        "id": "b_006", "thread_id": "b_005",
        "project": "Battery B-800", "channel": "thermal-testing",
        "user": "sarah.chen",
        "text": "Directly caused by Alex's baseplate shift. Airflow path over the heat sink array is now partially blocked."
    },
    {
        "id": "b_007", "thread_id": "b_005",
        "project": "Battery B-800", "channel": "thermal-testing",
        "user": "tom.harris",
        "text": "Trialing Gap Pad 5000S35 from Bergquist as mitigation. Conductivity is 5x the current TIM. Should buy us 6-8 degrees."
    },
    {
        "id": "b_008", "thread_id": "b_005",
        "project": "Battery B-800", "channel": "thermal-testing",
        "user": "priya.kumar",
        "text": "Any change to the TIM requires a new qualification run per our DVT test plan. That is a minimum 2-day test cycle."
    },

    # Thread 3: Supply Chain Risk (in #supply-chain-alerts)
    {
        "id": "b_009", "thread_id": None,
        "project": "Battery B-800", "channel": "supply-chain-alerts",
        "user": "jason.wu",
        "text": "Taiwan Motor Corp confirmed: custom copper heat sinks have a 6-week lead time. If engineering needs a redesign, I need a PO approved by Friday EOD to hit the June production window."
    },
    {
        "id": "b_010", "thread_id": "b_009",
        "project": "Battery B-800", "channel": "supply-chain-alerts",
        "user": "raj.sharma",
        "text": "6-week lead pushes us past June production. We will incur $80K in CM penalty fees for missing the agreed build slot. Escalating to CFO."
    },
    {
        "id": "b_011", "thread_id": "b_009",
        "project": "Battery B-800", "channel": "supply-chain-alerts",
        "user": "jason.wu",
        "text": "I have a secondary source in Shenzhen but they have not been qualified. Can QA fast-track a supplier qualification?"
    },
    {
        "id": "b_012", "thread_id": "b_009",
        "project": "Battery B-800", "channel": "supply-chain-alerts",
        "user": "priya.kumar",
        "text": "Fast-track supplier qual is possible but it requires sign-off from VP Quality. Minimum 5 business days."
    },

    # Thread 4: PM Status (in #general)
    {
        "id": "b_013", "thread_id": None,
        "project": "Battery B-800", "channel": "general",
        "user": "lisa.morgan",
        "text": "DVT design freeze was Friday. Given the thermal blocker and supply chain risk, I am calling an emergency design review for tomorrow 9AM. All leads required."
    },
    {
        "id": "b_014", "thread_id": "b_013",
        "project": "Battery B-800", "channel": "general",
        "user": "alex.johnson",
        "text": "Confirmed. I will have a revised CAD and clearance analysis ready before the meeting."
    },
    {
        "id": "b_015", "thread_id": "b_013",
        "project": "Battery B-800", "channel": "general",
        "user": "tom.harris",
        "text": "I will bring the Gap Pad simulation results. If it passes we might be able to avoid a full redesign."
    },
    # Design Debt demo message — triggers the Design Debt Alert
    {
        "id": "b_016", "thread_id": "b_013",
        "project": "Battery B-800", "channel": "general",
        "user": "alex.johnson",
        "text": "For now I shimmed the thermal pad to buy us clearance. It is a workaround until the revised housing lands. Need an ECO filed before DVT freeze."
    },

    # ─────────────────────────────────────────────────────────────
    # PROJECT: Actuator A-1 | Phase: EVT (Prototyping)
    # Scenario: Joint torque failure during load testing
    # ─────────────────────────────────────────────────────────────

    # Thread 1: Torque Failure
    {
        "id": "a_001", "thread_id": None,
        "project": "Actuator A-1", "channel": "arm-actuators",
        "user": "mike.patel",
        "text": "Elbow joint throwing Error 0xA4 (Over-Torque Protection) during 10kg lift tests at full extension. Seeing gear slippage. Not expected at this EVT stage."
    },
    {
        "id": "a_002", "thread_id": "a_001",
        "project": "Actuator A-1", "channel": "arm-actuators",
        "user": "alex.johnson",
        "text": "H-40 harmonic drive is rated 85Nm peak. What are we actually logging at 10kg extension?"
    },
    {
        "id": "a_003", "thread_id": "a_001",
        "project": "Actuator A-1", "channel": "arm-actuators",
        "user": "mike.patel",
        "text": "Telemetry shows 92Nm at full extension. We are 8% over the drive spec. Either we drop the payload target or redesign the gear ratio."
    },
    {
        "id": "a_004", "thread_id": "a_001",
        "project": "Actuator A-1", "channel": "arm-actuators",
        "user": "sarah.chen",
        "text": "The motor driver board is also seeing voltage spikes when the over-torque trips. Might be damaging the FETs. I will scope it tomorrow."
    },

    # Thread 2: Vendor & Parts
    {
        "id": "a_005", "thread_id": None,
        "project": "Actuator A-1", "channel": "supply-chain-alerts",
        "user": "jason.wu",
        "text": "If we need a different gear ratio from Harmonic Drive AG, the next available model (H-50) has a 10-week lead time. No stock in NA."
    },
    {
        "id": "a_006", "thread_id": "a_005",
        "project": "Actuator A-1", "channel": "supply-chain-alerts",
        "user": "lisa.morgan",
        "text": "10 weeks blows up the DVT schedule entirely. Can we reduce payload spec to 8kg to stay within the H-40 limits for EVT?"
    },

    # ─────────────────────────────────────────────────────────────
    # PROJECT: Chassis C-200 | Phase: Concept
    # Scenario: Early-stage material selection discussion
    # ─────────────────────────────────────────────────────────────

    # Thread 1: Material Selection
    {
        "id": "c_001", "thread_id": None,
        "project": "Chassis C-200", "channel": "chassis-design",
        "user": "alex.johnson",
        "text": "Starting material trade study for the C-200 frame. Comparing 6061-T6 aluminum vs carbon fiber composite. CFRP is 40% lighter but 3x the cost."
    },
    {
        "id": "c_002", "thread_id": "c_001",
        "project": "Chassis C-200", "channel": "chassis-design",
        "user": "mike.patel",
        "text": "Payload capacity requirements will drive this. If we are targeting 25kg field payload, CFRP is worth it for the weight savings."
    },
    {
        "id": "c_003", "thread_id": "c_001",
        "project": "Chassis C-200", "channel": "chassis-design",
        "user": "raj.sharma",
        "text": "CFRP cost delta is $1,200/unit. At 500 units/year run rate that is $600K annually. Need product to justify that margin impact."
    },
    {
        "id": "c_004", "thread_id": "c_001",
        "project": "Chassis C-200", "channel": "chassis-design",
        "user": "ben.carter",
        "text": "Weight savings is a huge selling point for field ops. If CFRP gets us under 15kg total robot weight that is a genuine differentiator vs the competition."
    },

    # Thread 2: Timeline
    {
        "id": "c_005", "thread_id": None,
        "project": "Chassis C-200", "channel": "general",
        "user": "lisa.morgan",
        "text": "C-200 Concept Review is scheduled for May 15th. We need material selection locked and a preliminary BOM by then. Who owns the BOM?"
    },
    {
        "id": "c_006", "thread_id": "c_005",
        "project": "Chassis C-200", "channel": "general",
        "user": "jason.wu",
        "text": "I will own the BOM but I need the material selection from Alex first. Alex, can you have a recommendation by May 8th?"
    },

    # ─────────────────────────────────────────────────────────────
    # EXTERNAL VENDOR COMMUNICATIONS (Slack Connect channels)
    # Vendors only see logistics/schedule — not internal engineering
    # ─────────────────────────────────────────────────────────────

    # Taiwan Motor Corp <> Battery B-800 (vendor-connect channel)
    {
        "id": "v_001", "thread_id": None,
        "project": "Battery B-800", "channel": "vendor-connect-battery",
        "user": "tmcorp.procurement",
        "text": "Confirming updated lead time for the copper heat sink batch: 6 weeks from PO receipt. We can expedite to 4 weeks for a 15% surcharge. Please advise."
    },
    {
        "id": "v_002", "thread_id": "v_001",
        "project": "Battery B-800", "channel": "vendor-connect-battery",
        "user": "jason.wu",
        "text": "Understood. Hold capacity for now. We have an internal design review tomorrow that may change the spec. Will confirm PO details by end of week."
    },

    # Harmonic Drive AG <> Actuator A-1 (vendor-connect channel)
    {
        "id": "v_003", "thread_id": None,
        "project": "Actuator A-1", "channel": "vendor-connect-actuator",
        "user": "hdrive.ag",
        "text": "We have reviewed your torque requirements. The H-40 is rated 85Nm continuous, 95Nm peak (10s). If you are seeing 92Nm steady-state you are outside our rated envelope. The H-50 model supports 120Nm and is available with a 10-week lead time."
    },
    {
        "id": "v_004", "thread_id": "v_003",
        "project": "Actuator A-1", "channel": "vendor-connect-actuator",
        "user": "jason.wu",
        "text": "Thanks for the clarification. Can you hold 5 units of the H-50 pending our engineering review? We will confirm the order by Friday."
    },
    {
        "id": "v_005", "thread_id": "v_003",
        "project": "Actuator A-1", "channel": "vendor-connect-actuator",
        "user": "hdrive.ag",
        "text": "We can hold 5 units for 72 hours. After that they return to open stock. Please confirm before Friday noon ET."
    },

    # Apex Fabrication <> Chassis C-200 (vendor-connect channel)
    {
        "id": "v_006", "thread_id": None,
        "project": "Chassis C-200", "channel": "vendor-connect-chassis",
        "user": "apexfab.ops",
        "text": "We can quote both 6061-T6 aluminum and CFRP for the C-200 frame. We need a finalized drawing package to provide accurate pricing. What is your target quote date?"
    },
    {
        "id": "v_007", "thread_id": "v_006",
        "project": "Chassis C-200", "channel": "vendor-connect-chassis",
        "user": "jason.wu",
        "text": "Material selection is being finalized by May 8th. We will send the drawing package by May 10th. Can you turn around a quote within 5 business days?"
    },

    # ─────────────────────────────────────────────────────────────
    # NOISE MESSAGES: Real-world clutter that MUST be filtered out
    # These score 0 and are routed to separate logs, NOT the digest
    # ─────────────────────────────────────────────────────────────

    # Off-Topic: Social/casual chatter in project channels
    {
        "id": "n_001", "thread_id": None,
        "project": "Battery B-800", "channel": "battery-design",
        "user": "alex.johnson",
        "text": "Hey team, anyone grabbing lunch from the taco place today? Last day they are open before renovation.",
        "noise_type": "Off-Topic"
    },
    {
        "id": "n_002", "thread_id": None,
        "project": "Actuator A-1", "channel": "arm-actuators",
        "user": "mike.patel",
        "text": "Did anyone catch the game last night? What a finish.",
        "noise_type": "Off-Topic"
    },

    # Platform/IT Issues: Slack itself failing
    {
        "id": "n_003", "thread_id": None,
        "project": "Battery B-800", "channel": "general",
        "user": "sarah.chen",
        "text": "Is Slack being slow for everyone? My messages are not sending and I keep getting a connection error.",
        "noise_type": "Platform/IT"
    },
    {
        "id": "n_004", "thread_id": None,
        "project": "Actuator A-1", "channel": "vendor-connect-actuator",
        "user": "jason.wu",
        "text": "I tried sending files to harmonic_drive_ag but the upload keeps failing with a 403 error. IT ticket submitted.",
        "noise_type": "Platform/IT"
    },

    # HR/Admin: Org-level announcements in project channels
    {
        "id": "n_005", "thread_id": None,
        "project": "Chassis C-200", "channel": "general",
        "user": "lisa.morgan",
        "text": "Reminder from HR: Q2 performance self-reviews are due by May 15th. Please complete them in Workday.",
        "noise_type": "HR/Admin"
    },
    {
        "id": "n_006", "thread_id": None,
        "project": "Battery B-800", "channel": "general",
        "user": "lisa.morgan",
        "text": "Company all-hands is rescheduled to Thursday 3PM PT. Zoom link in the calendar invite.",
        "noise_type": "HR/Admin"
    },

    # Access Management: Vendor losing Slack access
    {
        "id": "n_007", "thread_id": None,
        "project": "Actuator A-1", "channel": "vendor-connect-actuator",
        "user": "jason.wu",
        "text": "harmonic_drive_ag has not responded in 3 days and their Slack Connect invite shows as expired. I have emailed their account manager. Will update.",
        "noise_type": "Access Management"
    },
    {
        "id": "n_008", "thread_id": None,
        "project": "Battery B-800", "channel": "vendor-connect-battery",
        "user": "jason.wu",
        "text": "taiwan_vendor flagged that they lost access to this Slack Connect channel after their IT did an account reset. Re-sending the invite now.",
        "noise_type": "Access Management"
    }
]


output_path = "enterprise_logic.json"
with open(output_path, "w") as f:
    json.dump({
        "projects": projects,
        "weights": complex_weights,
        "messages": mock_messages
    }, f, indent=4)

print(f"Enterprise data generated:")
print(f"  {len(projects)} projects")
print(f"  {len(mock_messages)} Slack messages")
print(f"  {len(complex_weights)} roles in weighting matrix")
