# 🧭 Safar AI — Smart Route Predictor

> **Pakistan's first AI-powered smart route predictor.** Predicts road blockages using ML & NLP, calculates real-time fuel costs in PKR, scores route safety, generates Smart Travel Reports via Groq AI, and answers queries in Urdu/English via AI agent "Raasta".

[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Powered%20by-Groq%20AI-00D4AA)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🛰️ **Smart Multi-Route Fetching** | Fetches up to 3 alternative routes via OpenRouteService API |
| 🧠 **AI Scoring Engine** | Weighted scoring (time, distance, safety, congestion, cost) |
| 🤖 **ML Blockage Predictor** | XGBoost model trained on Pakistan traffic patterns |
| 🗺️ **Interactive Map** | Folium dark map with color-coded routes, blockage markers, rest areas |
| 📊 **Analytics Dashboard** | Plotly charts — route comparison, safety gauge, cost breakdown, ETA bars |
| 📝 **Groq AI Travel Report** | Deep analysis via Llama 3.3 70B with risks, tips, and recommendations |
| 💬 **Raasta Chatbot** | AI travel assistant (English + Urdu) with route-context awareness |
| 📥 **Downloadable Reports** | Professional HTML travel report with one-click download |
| 📜 **Route History** | Session-based search history with comparison |
| 🛡️ **Safety Index** | Region + time + road type scoring (0-100 scale) |
| 💰 **PKR Cost Calculator** | Fuel + toll estimation for 8 vehicle types |

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Safar-AI-Smart-Route-Predictor.git
cd Safar-AI-Smart-Route-Predictor
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up API Keys

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

| Key | Source | Free? |
|---|---|---|
| `ORS_API_KEY` | [openrouteservice.org](https://openrouteservice.org) | ✅ 2,000 req/day |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | ✅ Free tier |

### 4. Run the App

```bash
streamlit run app.py
```

---

## 📁 Project Structure

```
├── app.py                  # Main Streamlit entry point
├── agent/                  # Raasta AI Chatbot
│   ├── raasta.py           # Chat logic with Groq
│   ├── intent.py           # Intent classification
│   └── language.py         # Urdu/English detection
├── engine/                 # Route Intelligence Engine
│   ├── routing.py          # ORS API integration
│   ├── scoring.py          # Weighted route scoring
│   ├── safety.py           # Safety index calculator
│   ├── cost.py             # Fuel & toll cost (PKR)
│   ├── eta.py              # ETA with congestion
│   └── blockage.py         # Blockage zone checker
├── ml/                     # Machine Learning
│   ├── train_blockage.py   # XGBoost training
│   └── predict.py          # Blockage inference
├── map/                    # Map Visualization
│   ├── base_map.py         # Folium dark map
│   ├── route_layer.py      # Route polylines
│   ├── blockage_layer.py   # Blockage markers
│   └── poi_layer.py        # Rest area markers
├── groq_ai/                # Groq LLM Integration
│   ├── report.py           # Travel report generator
│   └── chat.py             # Chat completion wrapper
├── dashboard/              # Charts & Widgets
│   ├── charts.py           # Plotly visualizations
│   └── widgets.py          # Streamlit UI components
├── email_service/          # Email Reports
│   └── sender.py           # Gmail SMTP sender
├── database/               # Session History
│   └── db.py               # JSON session storage
├── data/                   # Static Data Files
│   ├── pakistan_cities.json # 30 cities with coords
│   ├── fuel_prices.json    # PKR fuel & toll rates
│   ├── vehicle_config.json # 8 vehicle types
│   ├── safety_index.json   # Regional safety scores
│   ├── blockages.json      # Known blockage hotspots
│   └── rest_areas.json     # Motorway rest stops
└── utils/                  # Shared Utilities
    └── helpers.py          # Geocoding, formatting
```

---

## 🧮 Route Scoring Algorithm

```
Score = (0.30 × Time) + (0.15 × Distance) + (0.25 × Safety) + (0.20 × Congestion) + (0.10 × Cost)
```

Each factor is normalized to 0-100. The highest scoring route is recommended.

---

## 🌐 Streamlit Cloud Deployment

1. Push your repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and set `app.py` as the main file
4. Add secrets in **Settings → Secrets**:

```toml
ORS_API_KEY = "your_key"
GROQ_API_KEY = "your_key"
```

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **Maps:** Folium + streamlit-folium
- **Routing:** OpenRouteService API
- **LLM:** Groq (Llama 3.3 70B Versatile)
- **ML:** XGBoost + scikit-learn
- **Charts:** Plotly
- **Reports:** Downloadable HTML reports
- **NLP:** langdetect + fuzzywuzzy

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with ❤️ in Pakistan — <strong>Safar AI</strong> © 2026
</p>
