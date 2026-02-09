# 📦 TechShip Tracking Dashboard

Real-time shipment tracking with PIN-protected client access for 18 Wheels Logistics.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://raymondli18w-techshiptechtrack1.streamlit.app)

## ✨ Features

- 🔐 **PIN-Protected Access** - Client isolation (BS04, CB05, JS03, MR01)
- 🔍 **Multi-Term Search** - Paste multiple search terms (one per line)
- ⚙️ **Column Selection** - Customize displayed columns
- 📅 **Advanced Filters** - Date range, status, service type
- 📱 **Live Tracking API** - 100% independent real-time carrier lookups
- 🔄 **Hourly Auto-Updates** - Fresh data synced from local PC

## 🔑 Client PINs

| Client | PIN |
|--------|-----|
| BS04 | `bs04ts` |
| CB05 | `cb05ts` |
| JS03 | `js03ts` |
| MR01 | `mr01ts` |

## 🚀 Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit app
streamlit run streamlit_app.py