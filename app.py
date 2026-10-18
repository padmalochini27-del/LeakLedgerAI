
import json
from datetime import datetime

import pandas as pd
import streamlit as st

try:
    import ollama
except ImportError:
    ollama = None


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="LeakLedger AI",
    page_icon="⚡",
    layout="wide",
)


# =========================================================
# STYLING - HIGH CONTRAST, READABLE TEXT
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #F7F8F2;
        color: #26352C;
    }

    .block-container {
        max-width: 1120px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* General text */
    .stApp p,
    .stApp li,
    .stApp label,
    .stApp [data-testid="stMarkdownContainer"] p {
        color: #26352C;
    }

    /* Section headings */
    .stApp h1,
    .stApp h2,
    .stApp h3,
    .stApp h4 {
        color: #173D32 !important;
    }

    /* Hero banner */
    .hero {
        background: linear-gradient(120deg, #173D32, #34765A);
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 24px;
    }

    .hero h1 {
        color: #FFFFFF !important;
        font-size: 2.5rem;
    }

    .hero p {
        color: #FFFFFF !important;
        font-size: 1.05rem;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #C9D9CC;
        border-radius: 14px;
        padding: 18px;
    }

    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] label p,
    div[data-testid="stMetricLabel"] p {
        color: #385447 !important;
        opacity: 1 !important;
    }

    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] *,
    div[data-testid="stMetricDelta"] {
        color: #173D32 !important;
        opacity: 1 !important;
    }

    /* Data table text */
    div[data-testid="stDataFrame"] {
        color: #26352C !important;
    }

    div[data-testid="stDataFrame"] * {
        color: #26352C;
    }

    /* Inputs */
    .stTextInput label,
    .stNumberInput label,
    .stSelectbox label,
    .stDataEditor label {
        color: #26352C !important;
    }

    /* Expander */
    div[data-testid="stExpander"] {
        border-color: #C9D9CC;
    }

    /* Helpful notes */
    div[data-testid="stAlert"] p {
        color: #26352C !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">
        <h1>⚡ LeakLedger AI</h1>
        <p>
            Investigate household electricity use.
            Understand the numbers. Find what to check next.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "A local-first electricity investigation assistant. "
    "Estimates use the values you enter, not live meter readings."
)


# =========================================================
# 1. APPLIANCE INPUTS
# =========================================================

st.subheader("🏠 1. Your household appliances")

st.write(
    "Edit the sample appliances or add your own. "
    "Use rated wattage when available."
)

DEFAULT_APPLIANCES = [
    {
        "Appliance": "Air conditioner",
        "Power (W)": 1200,
        "Hours per day": 6.0,
        "Quantity": 1,
    },
    {
        "Appliance": "Refrigerator",
        "Power (W)": 150,
        "Hours per day": 8.0,
        "Quantity": 1,
    },
    {
        "Appliance": "Ceiling fan",
        "Power (W)": 75,
        "Hours per day": 10.0,
        "Quantity": 3,
    },
    {
        "Appliance": "LED lights",
        "Power (W)": 10,
        "Hours per day": 5.0,
        "Quantity": 5,
    },
    {
        "Appliance": "Laptop",
        "Power (W)": 65,
        "Hours per day": 6.0,
        "Quantity": 1,
    },
]

if "appliances" not in st.session_state:
    st.session_state.appliances = pd.DataFrame(
        DEFAULT_APPLIANCES
    )

edited = st.data_editor(
    st.session_state.appliances,
    num_rows="dynamic",
    use_container_width=True,
    key="appliance_editor",
    column_config={
        "Appliance": st.column_config.TextColumn(
            "Appliance",
            required=True,
        ),
        "Power (W)": st.column_config.NumberColumn(
            "Power (W)",
            min_value=0,
            max_value=100000,
            step=1,
            required=True,
        ),
        "Hours per day": st.column_config.NumberColumn(
            "Hours per day",
            min_value=0,
            max_value=24,
            step=0.5,
            required=True,
        ),
        "Quantity": st.column_config.NumberColumn(
            "Quantity",
            min_value=1,
            max_value=100,
            step=1,
            required=True,
        ),
    },
)

st.session_state.appliances = edited.copy()


# =========================================================
# 2. ELECTRICITY TARIFF
# =========================================================

st.subheader("💰 2. Electricity tariff")

col_a, col_b = st.columns(2)

with col_a:
    tariff = st.number_input(
        "Cost per kWh (₹)",
        min_value=0.0,
        value=8.0,
        step=0.5,
        help="Enter your approximate effective cost per unit.",
    )

with col_b:
    days = st.number_input(
        "Days to estimate",
        min_value=1,
        max_value=366,
        value=30,
        step=1,
    )

st.caption(
    "One electricity unit equals one kWh. Actual bills can include "
    "tariff slabs, fixed charges, taxes, and other fees."
)


# =========================================================
# 3. PYTHON CALCULATIONS
# =========================================================

df = edited.copy()

if not df.empty:
    df["Appliance"] = (
        df["Appliance"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    for column in [
        "Power (W)",
        "Hours per day",
        "Quantity",
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        ).fillna(0)

    df = df[df["Appliance"] != ""].copy()

    df["Daily kWh"] = (
        df["Power (W)"]
        * df["Hours per day"]
        * df["Quantity"]
        / 1000
    )

    df["Estimated kWh"] = df["Daily kWh"] * days

    df["Estimated cost (₹)"] = (
        df["Estimated kWh"] * tariff
    )

else:
    df = pd.DataFrame(
        columns=[
            "Appliance",
            "Power (W)",
            "Hours per day",
            "Quantity",
            "Daily kWh",
            "Estimated kWh",
            "Estimated cost (₹)",
        ]
    )

daily_total = (
    float(df["Daily kWh"].sum())
    if not df.empty
    else 0.0
)

period_total = (
    float(df["Estimated kWh"].sum())
    if not df.empty
    else 0.0
)

period_cost = (
    float(df["Estimated cost (₹)"].sum())
    if not df.empty
    else 0.0
)

if not df.empty and period_total > 0:
    df["Share (%)"] = (
        df["Estimated kWh"] / period_total * 100
    )

    ranked = df.sort_values(
        by=["Estimated kWh", "Appliance"],
        ascending=[False, True],
    ).copy()

else:
    df["Share (%)"] = 0.0
    ranked = df.copy()


# =========================================================
# 4. ESTIMATED CONSUMPTION - VISIBLE DASHBOARD
# =========================================================

st.divider()

st.subheader("📊 3. Estimated consumption")

st.markdown("### Your calculated results")

metric_a, metric_b, metric_c = st.columns(3)

with metric_a:
    st.metric(
        "Daily energy",
        f"{daily_total:.2f} kWh",
    )

with metric_b:
    st.metric(
        f"Energy over {int(days)} days",
        f"{period_total:.2f} kWh",
    )

with metric_c:
    st.metric(
        f"Estimated cost over {int(days)} days",
        f"₹{period_cost:,.2f}",
    )

st.markdown("### Appliance consumption breakdown")

if ranked.empty:

    st.info(
        "Add an appliance above to see its estimated consumption."
    )

else:

    breakdown_columns = [
        "Appliance",
        "Daily kWh",
        "Estimated kWh",
        "Share (%)",
        "Estimated cost (₹)",
    ]

    breakdown = ranked[breakdown_columns].copy()

    breakdown = breakdown.rename(
        columns={
            "Daily kWh": "Daily energy (kWh)",
            "Estimated kWh": f"Energy ({int(days)} days, kWh)",
            "Share (%)": "Share (%)",
            "Estimated cost (₹)": "Estimated cost (₹)",
        }
    )

    st.dataframe(
        breakdown.style.format(
            {
                "Daily energy (kWh)": "{:.2f}",
                f"Energy ({int(days)} days, kWh)": "{:.2f}",
                "Share (%)": "{:.1f}%",
                "Estimated cost (₹)": "₹{:.2f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    if period_total > 0:
        st.markdown("### Estimated energy by appliance")

        st.bar_chart(
            ranked.set_index("Appliance")["Estimated kWh"]
        )

        largest = ranked.iloc[0]

        st.markdown(
            f"**Largest estimated contributor:** "
            f"{largest['Appliance']} — "
            f"{largest['Estimated kWh']:.2f} kWh over "
            f"{int(days)} days "
            f"({largest['Share (%)']:.1f}% of the estimate)."
        )

        st.info(
            "A large estimated share does not establish waste or a fault. "
            "Verify actual use and power consumption before drawing "
            "conclusions."
        )

    else:
        st.info(
            "The current inputs produce zero estimated energy use. "
            "Check the entered wattage and usage hours."
        )

st.caption(
    "The metrics and table above are calculated by Python. "
    "They do not depend on the AI response."
)


# =========================================================
# 5. SAFE INVESTIGATION CHECKLIST
# =========================================================

st.subheader("🧭 4. Investigation checklist")

checklist = [
    (
        "Verify rated power",
        "Compare the entered wattage with the appliance label or manual.",
    ),
    (
        "Review operating hours",
        "Use a realistic estimate of how long the appliance operates.",
    ),
    (
        "Consider operating cycles",
        "Refrigerators and air conditioners may cycle on and off. "
        "Rated power multiplied by elapsed time can overestimate use.",
    ),
    (
        "Compare with actual readings",
        "Compare your estimates with meter readings or electricity bills "
        "covering the same period, where possible.",
    ),
    (
        "Investigate unusual changes",
        "Review changes in usage before concluding that an appliance "
        "is inefficient or faulty.",
    ),
    (
        "Keep electrical work safe",
        "Do not open equipment or attempt unsafe repairs. "
        "Consult a qualified electrician if you suspect a fault.",
    ),
]

for title, description in checklist:
    with st.expander(title):
        st.write(description)


# =========================================================
# 6. LOCAL AI INVESTIGATION
# =========================================================

st.subheader("🤖 5. Ask local AI to explain the results")

st.write(
    "Gemma runs through Ollama on your computer. "
    "Python calculates the figures; the model explains them."
)

question = st.text_input(
    "What would you like to understand?",
    value=(
        "Which appliance should I review first, "
        "and what should I check?"
    ),
)

if st.button(
    "Generate local AI investigation",
    type="primary",
):

    if ranked.empty:

        st.warning(
            "Add at least one named appliance before generating "
            "an investigation."
        )

    elif ollama is None:

        st.error(
            "The Ollama Python package is missing. "
            "Run: python -m pip install ollama"
        )

    else:

        appliance_records = []

        for _, row in ranked.iterrows():
            appliance_records.append(
                {
                    "appliance": str(row["Appliance"]),
                    "power_w": round(
                        float(row["Power (W)"]), 2
                    ),
                    "hours_per_day": round(
                        float(row["Hours per day"]), 2
                    ),
                    "quantity": int(row["Quantity"]),
                    "daily_kwh": round(
                        float(row["Daily kWh"]), 2
                    ),
                    "estimated_period_kwh": round(
                        float(row["Estimated kWh"]), 2
                    ),
                    "share_percent": round(
                        float(row["Share (%)"]), 2
                    ),
                    "estimated_cost_inr": round(
                        float(row["Estimated cost (₹)"]), 2
                    ),
                }
            )

        authoritative_data = {
            "estimate_days": int(days),
            "tariff_inr_per_kwh": round(
                float(tariff), 2
            ),
            "estimated_daily_energy_kwh": round(
                daily_total, 2
            ),
            "estimated_period_energy_kwh": round(
                period_total, 2
            ),
            "estimated_period_cost_inr": round(
                period_cost, 2
            ),
            "appliances_sorted_highest_to_lowest": appliance_records,
        }

        data_json = json.dumps(
            authoritative_data,
            ensure_ascii=False,
            indent=2,
        )

        prompt = f"""
You are LeakLedger AI, a cautious household electricity assistant.

The JSON below contains calculations performed by Python.
Treat these values as the sole source of numerical truth.

AUTHORITATIVE DATA:
{data_json}

USER QUESTION:
{question}

STRICT REQUIREMENTS:
1. Never change, recalculate, or contradict a supplied number.
2. The appliance list is sorted from highest to lowest estimated
   period energy use. Preserve that exact order.
3. Energy is measured in kWh. Cost is measured in INR (₹).
   Never describe a rupee amount as energy consumption.
4. These are estimates based on user-entered values, not live
   measurements or guaranteed future usage.
5. Do not invent readings, specifications, or savings.
6. A high estimated share does not prove waste or a fault.
7. Never suggest unsafe electrical repairs.
8. If the data cannot establish a claim, say so.

Use these headings:

### 1. Overall estimate
Explain the supplied daily energy, period energy, period length,
and estimated cost. Keep kWh and INR separate.

### 2. Largest estimated contributors
Discuss up to three appliances in the exact supplied order.
Use their supplied estimated kWh and share percentages.
Never call an appliance the largest unless it is listed first.

### 3. Practical checks
Give three safe checks about rated power, actual operating hours,
and comparison with meter readings or bills.

### 4. Limitations
Explain how real power draw, operating cycles, and household habits
can change actual use. The estimates cannot prove waste or a fault.

Use concise English. Do not invent figures.
"""

        try:

            with st.spinner(
                "Gemma is analysing your results locally..."
            ):

                response = ollama.chat(
                    model="gemma3:1b",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Explain supplied data carefully. "
                                "Never invent or alter numerical results."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    options={
                        "temperature": 0.1,
                    },
                )

            st.markdown("### Local AI investigation")

            st.warning(
                "This is an AI-generated explanation. "
                "The Python-calculated dashboard above is the "
                "authoritative source for all figures."
            )

            st.markdown(
                response["message"]["content"]
            )

            st.caption(
                "Verify estimates against actual meter readings, "
                "appliance documentation, and electricity bills."
            )

        except Exception as exc:

            st.error(
                "Could not connect to Ollama. Check that Ollama is "
                "running and that `ollama list` shows gemma3:1b."
            )

            st.code(str(exc))

            st.info(
                "The calculator, dashboard, chart, and CSV export "
                "remain available without the AI explanation."
            )


# =========================================================
# 7. CSV EXPORT
# =========================================================

st.subheader("📥 6. Export your investigation")

report = ranked.copy()

report["Tariff (₹/kWh)"] = tariff
report["Estimate days"] = int(days)
report["Report date"] = datetime.now().strftime("%Y-%m-%d")

csv_bytes = report.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="Download appliance report (CSV)",
    data=csv_bytes,
    file_name="leakledger_energy_report.csv",
    mime="text/csv",
)


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "LeakLedger AI provides estimates and general investigation guidance. "
    "It is not a live electricity meter, utility bill, certified energy "
    "audit, or electrical safety diagnostic."
)

st.caption(
    "The AI explanation runs through your local Ollama installation. "
    "The app is designed not to send your appliance data to a cloud AI "
    "service; other software on your computer may have its own data "
    "handling behaviour."
)
