import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime, timedelta
from urllib.parse import quote
from functools import lru_cache
import time
import re

st.set_page_config(page_title="TechShip Tracking Dashboard", layout="wide", page_icon="📦")

# TechTrack API config (from Streamlit Secrets)
try:
    TECHTRACK_BASE_URL = st.secrets["techtrack"]["base_url"]
    TECHTRACK_USER_KEY = st.secrets["techtrack"]["user_key"]
    TECHTRACK_API_KEY = st.secrets["techtrack"]["api_key"]
except:
    TECHTRACK_BASE_URL = "https://18wheels.techtrack.cloud/api/v2/event/get-by-tracking-numbers"
    TECHTRACK_USER_KEY = "5A9AB7A7E6BC16DB1C6025B4BFBCF4E2"
    TECHTRACK_API_KEY = "a888c3c1-6884-4e3d-aeb7-438c1b519b12"

CLIENT_PINS = {"BS04": "bs04ts", "CB05": "cb05ts", "JS03": "js03ts", "MR01": "mr01ts"}
DEFAULT_COLUMNS = ["Client_Code", "Client_Name", "CustomerOrder", "TransactionNumber", "ShipmentStatus", "Total_Shipping_Charge", "Routing_ServiceCode", "ShipToAddress_Name", "ShipToAddress_Address1", "Package_ExtendedTrackingNumber", "Package_PackageFreightCharge_ShippingChargeTotal", "ProcessedOn_PST", "EST", "Event_name"]

_last_call_time = 0
_RATE_LIMIT_DELAY = 0.05

@lru_cache(maxsize=1000)
def get_techtrack_event_live(tracking_number: str):
    global _last_call_time
    clean_tn = re.sub(r'[^a-zA-Z0-9]', '', tracking_number.strip().upper())
    if not clean_tn:
        return {"success": False, "error": "❌ Invalid tracking number format", "tracking_number": tracking_number, "original_input": tracking_number}
    try:
        current_time = time.time()
        elapsed = current_time - _last_call_time
        if elapsed < _RATE_LIMIT_DELAY:
            time.sleep(_RATE_LIMIT_DELAY - elapsed)
        url = f"{TECHTRACK_BASE_URL}?TrackingNumbers=    {quote(clean_tn)}"
        headers = {"x-user-key": TECHTRACK_USER_KEY, "x-api-key": TECHTRACK_API_KEY, "User-Agent": "TechShipDashboard/1.0"}
        response = requests.get(url, headers=headers, timeout=15)
        _last_call_time = time.time()
        if response.status_code == 429:
            time.sleep(1)
            response = requests.get(url, headers=headers, timeout=15)
            _last_call_time = time.time()
        if response.status_code == 200:
            data = response.json()
            events = data.get("events", []) if isinstance(data, dict) else []
            if events and isinstance(events, list) and len(events) > 0:
                event = events[0]
                return {"success": True, "tracking_number": clean_tn, "original_input": tracking_number, "event_name": str(event.get("name", "Unknown")).strip(), "event_description": str(event.get("description", "No details")).strip(), "event_category": str(event.get("category", "Generic")).strip(), "event_dateTime_local": str(event.get("dateTime", {}).get("local", "N/A") if isinstance(event.get("dateTime"), dict) else "N/A").strip(), "event_dateTime_utc": str(event.get("dateTime", {}).get("utc", "N/A") if isinstance(event.get("dateTime"), dict) else "N/A").strip(), "event_accessLevel": str(event.get("accessLevel", "Public")).strip(), "event_location_city": str(event.get("location", {}).get("city", "") if isinstance(event.get("location"), dict) else "").strip(), "event_location_state": str(event.get("location", {}).get("state", "") if isinstance(event.get("location"), dict) else "").strip(), "carrier_retention_note": "✅ Data available (within carrier retention period)"}
            else:
                return {"success": False, "tracking_number": clean_tn, "original_input": tracking_number, "error": "⚠️ No tracking events found", "carrier_retention_note": "ℹ️ Carriers typically purge tracking data after 90-180 days. This number may be too old."}
        error_map = {401: "❌ Authentication failed - invalid API credentials", 403: "❌ Access denied - check API permissions", 404: f"❌ Tracking number '{clean_tn}' not found in carrier system", 429: "⚠️ Rate limit exceeded - please wait 1 second", 500: "⚠️ TechTrack server error - try again later"}
        return {"success": False, "tracking_number": clean_tn, "original_input": tracking_number, "error": error_map.get(response.status_code, f"⚠️ HTTP {response.status_code}: {response.reason}"), "carrier_retention_note": ""}
    except requests.exceptions.Timeout:
        return {"success": False, "tracking_number": clean_tn, "original_input": tracking_number, "error": "⚠️ Request timeout - carrier server slow", "carrier_retention_note": ""}
    except requests.exceptions.ConnectionError:
        return {"success": False, "tracking_number": clean_tn, "original_input": tracking_number, "error": "⚠️ Connection failed - check internet", "carrier_retention_note": ""}
    except Exception as e:
        return {"success": False, "tracking_number": clean_tn, "original_input": tracking_number, "error": f"⚠️ Unexpected error: {str(e)[:80]}", "carrier_retention_note": ""}

@st.cache_data(ttl=3600)
def load_master_database():
    prod_path = "master_database.xlsx"
    local_path = r"C:\Users\RaymondLi\OneDrive - 18wheels.ca\downloads may 30 2023\test6\2026\feb 2026 1\master_database\master_database.xlsx"
    if os.path.exists(prod_path):
        try:
            return pd.read_excel(prod_path)
        except Exception as e:
            st.warning(f"⚠️ Error loading production database: {str(e)[:100]}")
    if os.path.exists(local_path):
        try:
            return pd.read_excel(local_path)
        except Exception as e:
            st.warning(f"⚠️ Error loading local database: {str(e)[:100]}")
    st.error("❌ No database found. Admin: Run hourly update script on your PC to push data to GitHub.")
    return None

st.title("📦 TechShip Tracking Dashboard")
st.caption("Real-time shipment tracking with PIN-protected client access")

if 'authenticated_client' not in st.session_state:
    st.session_state.authenticated_client = None

if not st.session_state.authenticated_client:
    st.subheader("🔐 Client Access")
    pin = st.text_input("Client PIN", type="password", placeholder="Example: bs04ts, cb05ts, js03ts, mr01ts")
    if pin:
        for client_code, client_pin in CLIENT_PINS.items():
            if pin.strip().lower() == client_pin.lower():
                st.session_state.authenticated_client = client_code
                st.success(f"✅ Welcome! Viewing data for {client_code}")
                st.rerun()
        st.error("❌ Invalid PIN. Please check with your account manager.")
    st.stop()

df_master = load_master_database()
if df_master is None:
    st.stop()

if 'Client_Code' not in df_master.columns:
    st.error("❌ Database missing 'Client_Code' column. Contact administrator.")
    st.stop()

df = df_master[df_master['Client_Code'] == st.session_state.authenticated_client].copy()
total_rows = len(df)

if total_rows == 0:
    st.warning(f"📭 No shipments found for client {st.session_state.authenticated_client}")
    st.stop()

with st.sidebar:
    st.markdown("### 🔍 Filters")
    if 'ProcessedOn_PST' in df.columns:
        df['ProcessedOn_PST_dt'] = pd.to_datetime(df['ProcessedOn_PST'], errors='coerce')
        valid_dates = df['ProcessedOn_PST_dt'].dropna()
        if len(valid_dates) > 0:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            use_date_filter = st.checkbox("📅 Date Range", value=False)
            if use_date_filter:
                start_date = st.date_input("From", value=max(min_date, max_date - timedelta(days=30)), min_value=min_date, max_value=max_date)
                end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)
                if start_date <= end_date:
                    mask = (df['ProcessedOn_PST_dt'] >= pd.Timestamp(start_date)) & (df['ProcessedOn_PST_dt'] <= pd.Timestamp(end_date) + pd.Timedelta(days=1))
                    df = df[mask]
    if 'ShipmentStatus' in df.columns:
        all_statuses = sorted(df['ShipmentStatus'].dropna().unique().tolist())
        selected_statuses = st.multiselect("📦 Shipment Status", options=all_statuses, default=all_statuses)
        if selected_statuses:
            df = df[df['ShipmentStatus'].isin(selected_statuses)]
    if st.button("↺ Reset Filters", use_container_width=True):
        st.rerun()
    st.markdown("---")
    st.markdown(f"### 📊 Results")
    st.metric("Total Shipments", f"{total_rows:,}")
    st.metric("Filtered Results", f"{len(df):,}")
    st.metric("Last Updated", datetime.now().strftime("%H:%M"))

st.subheader("🔍 Multi-Term Search")
search_terms = st.text_area("Search your shipments (one term per line)", height=60, placeholder="ABC\n12345\nVANCOUVER")
if search_terms.strip():
    terms = [t.strip() for t in search_terms.split('\n') if t.strip()]
    if terms:
        mask = pd.Series(False, index=df.index)
        for term in terms:
            term_mask = df.astype(str).apply(lambda col: col.str.contains(term, case=False, na=False)).any(axis=1)
            mask |= term_mask
        df = df[mask]
        st.info(f"🔍 Found {len(df):,} matching results")

st.subheader("⚙️ Display Columns")
available_cols = [col for col in DEFAULT_COLUMNS if col in df.columns] + [col for col in df.columns if col not in DEFAULT_COLUMNS]
selected_cols = st.multiselect("Select columns to display", options=available_cols, default=[col for col in DEFAULT_COLUMNS if col in df.columns])

if selected_cols and len(df) > 0:
    display_df = df[selected_cols].copy()
    if 'ShipmentStatus' in selected_cols:
        def color_status(val):
            if pd.isna(val): return ''
            v = str(val).lower()
            if 'delivered' in v: return 'background-color: #d4edda; color: #155724'
            if 'transit' in v or 'shipping' in v: return 'background-color: #fff3cd; color: #856404'
            if 'exception' in v: return 'background-color: #f8d7da; color: #721c24'
            return ''
        st.dataframe(display_df.style.applymap(color_status, subset=['ShipmentStatus']), use_container_width=True, height=min(600, 40 + len(display_df) * 35))
    else:
        st.dataframe(display_df, use_container_width=True, height=min(600, 40 + len(display_df) * 35))
    csv = display_df.to_csv(index=False)
    st.download_button("📥 Download Filtered Results (CSV)", csv, f"shipments_{st.session_state.authenticated_client}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", use_container_width=True)
    st.caption(f"✅ Showing {len(df):,} shipments | Filtered: {len(df):,} | Total: {total_rows:,}")
else:
    st.info("👆 Select columns above to view your shipment data")

st.markdown("---")
st.subheader("📱 LIVE TRACKING LOOKUP - 100% INDEPENDENT")
st.info("✅ **Works for ANY tracking number** - even if not in your database\n\n⚠️ **Note:** Carriers typically purge tracking data after **90-180 days**.")
col1, col2 = st.columns([4, 1])
with col1:
    track_input = st.text_input("Enter tracking number(s)", placeholder="398384333811 or 1Z90RR772032421756", label_visibility="collapsed")
with col2:
    search_btn = st.button("🔍 LIVE SEARCH", type="primary", use_container_width=True)
if (track_input.strip() or search_btn) and track_input.strip():
    raw_inputs = re.split(r'[,\s]+', track_input.strip())
    tracking_numbers = [tn for tn in raw_inputs if tn.strip()]
    if not tracking_numbers:
        st.error("❌ Please enter at least one valid tracking number")
    else:
        all_results = []
        with st.spinner(f"📡 Calling TechTrack API for {len(tracking_numbers)} number(s)..."):
            for tn in tracking_numbers:
                result = get_techtrack_event_live(tn)
                all_results.append(result)
        for i, result in enumerate(all_results, 1):
            st.markdown(f"### 📍 Result {i} of {len(all_results)}: `{result['original_input']}`")
            if result["success"]:
                col1, col2, col3 = st.columns(3)
                with col1:
                    status_lower = result["event_name"].lower()
                    emoji = "🟢" if "delivered" in status_lower else "🟡" if "transit" in status_lower else "🔵"
                    st.metric(f"{emoji} Status", result["event_name"])
                with col2:
                    st.metric("📅 Local Time", result["event_dateTime_local"])
                with col3:
                    loc = f"{result['event_location_city']}, {result['event_location_state']}".strip(", ")
                    st.metric("📍 Location", loc if loc != ", " else "Unknown")
                st.success(result["carrier_retention_note"])
                with st.expander("📋 Full Event Details"):
                    st.write(f"**Tracking Number:** `{result['tracking_number']}`")
                    st.write(f"**Category:** {result['event_category']}")
                    st.write(f"**UTC Time:** {result['event_dateTime_utc']}")
                    st.write(f"**Description:** {result['event_description']}")
            else:
                st.error(result["error"])
                if result.get("carrier_retention_note"):
                    st.info(result["carrier_retention_note"])
                st.markdown("#### ✅ Verified working test numbers:")
                st.code("398384333811          → Should show DELIVERED\n1Z90RR772032421756    → Should show live status")

st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("✅ Main table: Updated hourly from GitHub")
with col2:
    st.caption("⚡ Live tracking: Real-time API calls")
with col3:
    st.caption(f"🔄 Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} PST")
st.caption("**v2.0** | TechShip Tracking Dashboard | © 2026 18 Wheels Logistics")