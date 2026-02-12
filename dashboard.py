# import streamlit as st
# from truedata import TD_live
# from datetime import datetime as dt
# import pandas as pd
# import logging
# import time
# import math

# # =============================
# # PAGE CONFIG
# # =============================
# st.set_page_config(page_title="NIFTY Options Dashboard", layout="wide")
# st.title("📊 NIFTY Live Options Dashboard")

# # =============================
# # LOGIN
# # =============================
# username = "Trial165"
# password = "jenish165"

# @st.cache_resource
# def connect_truedata():
#     td = TD_live(username, password, log_level=logging.WARNING)
#     td.start_live_data(["NIFTY 50"])
#     return td

# td_obj = connect_truedata()

# # =============================
# # EXPIRY
# # =============================
# expiry_date = dt(2026, 2, 17)

# nifty_chain = td_obj.start_option_chain(
#     'NIFTY',
#     expiry_date,
#     chain_length=20,
#     bid_ask=True,
#     greek=True
# )

# # =============================
# # SIDEBAR SETTINGS
# # =============================
# refresh_rate = st.sidebar.slider("Refresh (seconds)", 1, 10, 2)

# st.sidebar.subheader("💰 Risk Management")
# capital = st.sidebar.number_input("Total Capital", value=100000)
# risk_percent = st.sidebar.slider("Risk % per Trade", 1, 100, 2)

# risk_amount = capital * (risk_percent / 100)
# st.sidebar.write(f"Max Risk per Trade: ₹ {risk_amount}")

# st.sidebar.subheader("🎯 Strike Selection")
# strike_mode = st.sidebar.selectbox(
#     "Strike Mode",
#     ["ATM", "OTM +50", "OTM +100"]
# )

# # =============================
# # LIVE PRICE
# # =============================
# live_data = td_obj.live_data
# ltp = None

# if live_data:
#     for key in live_data:
#         tick = live_data[key]
#         if tick.symbol == "NIFTY 50":
#             ltp = tick.ltp

# if ltp:
#     ltp = float(ltp)
#     st.metric("NIFTY 50 LTP", round(ltp, 2))

# # =============================
# # OPTION CHAIN
# # =============================
# chain_df = nifty_chain.get_option_chain()
# print(type(chain_df))

# if chain_df is not None and not chain_df.empty:

#     numeric_cols = ["strike", "iv", "delta", "gamma",
#                     "theta", "vega", "rho", "oi",
#                     "ltp", "last_price"]
#     for col in numeric_cols:
#         if col in chain_df.columns:
#             chain_df[col] = pd.to_numeric(chain_df[col], errors="coerce")

#     chain_df.fillna(0, inplace=True)

#     # =============================
#     # PCR
#     # =============================
#     if "type" in chain_df.columns and "oi" in chain_df.columns:
#         total_call_oi = chain_df[chain_df["type"] == "CE"]["oi"].sum()
#         total_put_oi = chain_df[chain_df["type"] == "PE"]["oi"].sum()
#         pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0
#         st.metric("Put Call Ratio (PCR)", round(pcr, 2))

#     # =============================
#     # RANGE ENGINE
#     # =============================
#     if ltp and "strike" in chain_df.columns:

#         chain_df["strike_diff"] = abs(chain_df["strike"] - ltp)
#         atm_row = chain_df.loc[chain_df["strike_diff"].idxmin()]
#         atm_strike = atm_row["strike"]

#         atm_calls = chain_df[(chain_df["strike"] == atm_strike) & (chain_df["type"] == "CE")]
#         atm_puts = chain_df[(chain_df["strike"] == atm_strike) & (chain_df["type"] == "PE")]

#         if not atm_calls.empty and not atm_puts.empty:

#             call_row = atm_calls.iloc[0]
#             put_row = atm_puts.iloc[0]

#             iv = call_row["iv"]
#             if iv > 1:
#                 iv = iv / 100

#             call_delta = call_row["delta"]
#             put_delta = put_row["delta"]
#             gamma = call_row["gamma"]

#             dte = (expiry_date - dt.now()).days
#             dte = max(dte, 1)

#             expected_move = ltp * iv * math.sqrt(dte / 365)

#             base_upper = ltp + expected_move
#             base_lower = ltp - expected_move

#             net_delta = call_delta - abs(put_delta)
#             bias_shift = net_delta * expected_move * 0.3

#             final_upper = base_upper + bias_shift
#             final_lower = base_lower + bias_shift

#             # =============================
#             # BIAS
#             # =============================
#             if net_delta > 0.02:
#                 bias = "Bullish"
#             elif net_delta < -0.02:
#                 bias = "Bearish"
#             else:
#                 bias = "Neutral"

#             # =============================
#             # CONFIDENCE
#             # =============================
#             if gamma > 0.001:
#                 confidence = "Low"
#             elif iv < 0.12:
#                 confidence = "High"
#             else:
#                 confidence = "Medium"

#             # =============================
#             # STRIKE SELECTION LOGIC
#             # =============================
#             strike_step = 0

#             if strike_mode == "OTM +50":
#                 strike_step = 50
#             elif strike_mode == "OTM +100":
#                 strike_step = 100

#             suggestion = "No Trade"
#             option_price = 0
#             qty = 0

#             if bias == "Bullish":
#                 target_strike = atm_strike + strike_step
#                 selected = chain_df[
#                     (chain_df["strike"] == target_strike) &
#                     (chain_df["type"] == "CE")
#                 ]
#             elif bias == "Bearish":
#                 target_strike = atm_strike - strike_step
#                 selected = chain_df[
#                     (chain_df["strike"] == target_strike) &
#                     (chain_df["type"] == "PE")
#                 ]
#             else:
#                 selected = pd.DataFrame()

#             if not selected.empty:
#                 row = selected.iloc[0]
#                 option_price = row.get("ltp", row.get("last_price", 0))
#                 option_price = float(option_price) if option_price else 0

#                 if option_price > 0:
#                     suggestion = f"Buy {row['type']} {int(target_strike)}"
#                     qty = int(risk_amount / option_price)

#             # =============================
#             # DISPLAY
#             # =============================
#             st.subheader("🎯 Weekly Range Prediction")
#             col1, col2, col3, col4 = st.columns(4)

#             col1.metric("Lower Bound", round(final_lower, 2))
#             col2.metric("Upper Bound", round(final_upper, 2))
#             col3.metric("Bias", bias)
#             col4.metric("Confidence", confidence)

#             st.subheader("📌 Trade Suggestion")
#             colA, colB, colC = st.columns(3)

#             colA.metric("Suggested Trade", suggestion)
#             colB.metric("Quantity", qty)
#             colC.metric("Capital Used", f"₹ {round(qty * option_price, 2)}")

#     # =============================
#     # OPTION CHAIN DISPLAY
#     # =============================
#     st.subheader("📈 Option Chain")
#     st.dataframe(chain_df.drop(columns=["strike_diff"], errors="ignore"),
#                  use_container_width=True)

# else:
#     st.warning("Option chain not available. Check expiry or subscription.")

# # # =============================
# # # REAL ACCURACY TRACKER
# # # =============================

# # st.subheader("📊 Model Accuracy Tracker")

# # if "predictions" not in st.session_state:
# #     st.session_state.predictions = []

# # today_date = dt.now().date()

# # # Save prediction once per day
# # if ltp and 'final_upper' in locals() and 'final_lower' in locals():

# #     if not any(p["date"] == today_date for p in st.session_state.predictions):

# #         st.session_state.predictions.append({
# #             "date": today_date,
# #             "lower": final_lower,
# #             "upper": final_upper,
# #             "result": None
# #         })

# # # Evaluate previous predictions
# # for p in st.session_state.predictions:
# #     if p["result"] is None:
# #         if ltp > p["upper"] or ltp < p["lower"]:
# #             p["result"] = "Broken"
# #         else:
# #             p["result"] = "Inside"

# # # Calculate accuracy
# # completed = [p for p in st.session_state.predictions if p["result"] is not None]

# # if completed:
# #     success = sum(1 for p in completed if p["result"] == "Inside")
# #     accuracy = success / len(completed) * 100
# # else:
# #     accuracy = 0

# # col1, col2 = st.columns(2)
# # col1.metric("Total Evaluated", len(completed))
# # col2.metric("Accuracy %", round(accuracy, 2))


# # =============================
# # AUTO REFRESH
# # =============================
# time.sleep(refresh_rate)
# st.rerun()
'''--------------------------------------------------------------------------------------------------------'''

import streamlit as st
from truedata import TD_live
from datetime import datetime as dt
import pandas as pd
import logging
import time
import math
import sqlite3
from datetime import datetime

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="NIFTY Options Dashboard", layout="wide")
st.title("📊 NIFTY Live Options Dashboard")

# =============================
# DATABASE SETUP
# =============================
conn = sqlite3.connect("dashboard_data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS nifty_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    ltp REAL,
    pcr REAL,
    lower_bound REAL,
    upper_bound REAL,
    bias TEXT,
    confidence TEXT,
    suggestion TEXT,
    quantity INTEGER,
    capital_used REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS option_chain (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    symbol TEXT,
    strike REAL,
    type TEXT,
    ltp REAL,
    volume REAL,
    oi INTEGER,
    oi_change INTEGER,
    iv REAL,
    delta REAL,
    gamma REAL,
    theta REAL,
    vega REAL,
    rho REAL
)
""")

conn.commit()

# =============================
# LOGIN
# =============================
username = "Trial165"
password = "jenish165"

@st.cache_resource
def connect_truedata():
    td = TD_live(username, password, log_level=logging.WARNING)
    td.start_live_data(["NIFTY 50"])
    return td

td_obj = connect_truedata()

# =============================
# EXPIRY
# =============================
expiry_date = dt(2026, 2, 17)

nifty_chain = td_obj.start_option_chain(
    'NIFTY',
    expiry_date,
    chain_length=20,
    bid_ask=True,
    greek=True
)

# =============================
# SIDEBAR SETTINGS
# =============================
refresh_rate = st.sidebar.slider("Refresh (seconds)", 1, 60, 30)

st.sidebar.subheader("💰 Risk Management")
capital = st.sidebar.number_input("Total Capital", value=100000)
risk_percent = st.sidebar.slider("Risk % per Trade", 1, 100, 2)

risk_amount = capital * (risk_percent / 100)
st.sidebar.write(f"Max Risk per Trade: ₹ {risk_amount}")

st.sidebar.subheader("🎯 Strike Selection")
strike_mode = st.sidebar.selectbox(
    "Strike Mode",
    ["ATM", "OTM +50", "OTM +100"]
)

# =============================
# LIVE PRICE
# =============================
live_data = td_obj.live_data
ltp = None

if live_data:
    for key in live_data:
        tick = live_data[key]
        if tick.symbol == "NIFTY 50":
            ltp = tick.ltp

if ltp:
    ltp = float(ltp)
    st.metric("NIFTY 50 LTP", round(ltp, 2))

# =============================
# OPTION CHAIN
# =============================
chain_df = nifty_chain.get_option_chain()

if chain_df is not None and not chain_df.empty:

    numeric_cols = ["strike", "iv", "delta", "gamma",
                    "theta", "vega", "rho", "oi",
                    "ltp", "last_price"]

    for col in numeric_cols:
        if col in chain_df.columns:
            chain_df[col] = pd.to_numeric(chain_df[col], errors="coerce")

    chain_df.fillna(0, inplace=True)

    # =============================
    # PCR
    # =============================
    total_call_oi = chain_df[chain_df["type"] == "CE"]["oi"].sum()
    total_put_oi = chain_df[chain_df["type"] == "PE"]["oi"].sum()
    pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0
    st.metric("Put Call Ratio (PCR)", round(pcr, 2))

    # =============================
    # RANGE ENGINE
    # =============================
    final_upper = final_lower = 0
    bias = "Neutral"
    confidence = "Low"
    suggestion = "No Trade"
    qty = 0
    option_price = 0

    if ltp and "strike" in chain_df.columns:

        chain_df["strike_diff"] = abs(chain_df["strike"] - ltp)
        atm_row = chain_df.loc[chain_df["strike_diff"].idxmin()]
        atm_strike = atm_row["strike"]

        atm_calls = chain_df[(chain_df["strike"] == atm_strike) & (chain_df["type"] == "CE")]
        atm_puts = chain_df[(chain_df["strike"] == atm_strike) & (chain_df["type"] == "PE")]

        if not atm_calls.empty and not atm_puts.empty:

            call_row = atm_calls.iloc[0]
            put_row = atm_puts.iloc[0]

            iv = call_row["iv"]
            if iv > 1:
                iv = iv / 100

            call_delta = call_row["delta"]
            put_delta = put_row["delta"]
            gamma = call_row["gamma"]

            dte = (expiry_date - dt.now()).days
            dte = max(dte, 1)

            expected_move = ltp * iv * math.sqrt(dte / 365)

            base_upper = ltp + expected_move
            base_lower = ltp - expected_move

            net_delta = call_delta - abs(put_delta)
            bias_shift = net_delta * expected_move * 0.3

            final_upper = base_upper + bias_shift
            final_lower = base_lower + bias_shift

            if net_delta > 0.02:
                bias = "Bullish"
            elif net_delta < -0.02:
                bias = "Bearish"

            if gamma > 0.001:
                confidence = "Low"
            elif iv < 0.12:
                confidence = "High"
            else:
                confidence = "Medium"

            strike_step = 0
            if strike_mode == "OTM +50":
                strike_step = 50
            elif strike_mode == "OTM +100":
                strike_step = 100

            if bias == "Bullish":
                target_strike = atm_strike + strike_step
                selected = chain_df[
                    (chain_df["strike"] == target_strike) &
                    (chain_df["type"] == "CE")
                ]
            elif bias == "Bearish":
                target_strike = atm_strike - strike_step
                selected = chain_df[
                    (chain_df["strike"] == target_strike) &
                    (chain_df["type"] == "PE")
                ]
            else:
                selected = pd.DataFrame()

            if not selected.empty:
                row = selected.iloc[0]
                option_price = float(row.get("ltp", 0))
                if option_price > 0:
                    suggestion = f"Buy {row['type']} {int(target_strike)}"
                    qty = int(risk_amount / option_price)

    # =============================
    # DISPLAY
    # =============================
    st.subheader("🎯 Weekly Range Prediction")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Lower Bound", round(final_lower, 2))
    col2.metric("Upper Bound", round(final_upper, 2))
    col3.metric("Bias", bias)
    col4.metric("Confidence", confidence)

    st.subheader("📌 Trade Suggestion")
    colA, colB, colC = st.columns(3)
    colA.metric("Suggested Trade", suggestion)
    colB.metric("Quantity", qty)
    colC.metric("Capital Used", f"₹ {round(qty * option_price, 2)}")

    # =============================
    # STORE DATA
    # =============================
    now = str(datetime.now())

    cursor.execute("""
        INSERT INTO nifty_snapshot
        (timestamp, ltp, pcr, lower_bound, upper_bound,
         bias, confidence, suggestion, quantity, capital_used)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now, ltp, pcr, final_lower, final_upper,
        bias, confidence, suggestion, qty, qty * option_price
    ))

    for _, row in chain_df.iterrows():
        cursor.execute("""
            INSERT INTO option_chain
            (timestamp, symbol, strike, type, ltp,
             volume, oi, oi_change, iv, delta,
             gamma, theta, vega, rho)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now,
            row.get("symbols"),
            row.get("strike"),
            row.get("type"),
            row.get("ltp"),
            row.get("volume"),
            row.get("oi"),
            row.get("oi_change"),
            row.get("iv"),
            row.get("delta"),
            row.get("gamma"),
            row.get("theta"),
            row.get("vega"),
            row.get("rho")
        ))

    conn.commit()

    # =============================
    # OPTION CHAIN DISPLAY
    # =============================
    st.subheader("📈 Option Chain")
    st.dataframe(chain_df.drop(columns=["strike_diff"], errors="ignore"),
                 use_container_width=True)

else:
    st.warning("Option chain not available.")

# =============================
# AUTO REFRESH
# =============================
time.sleep(refresh_rate)
st.rerun()
