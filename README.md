# 🍃 Air Quality Index (AQI) Forecasting System

A Machine Learning powered web application built with **Flask**, **Random Forest Regressor**, and modern **Frosted Glass UI** to forecast and analyze Air Quality Index (AQI) based on atmospheric pollutant concentrations.

---

## 🌟 Key Features

- 📊 **Interactive Dashboard**: Real-time visual monitoring of historical pollutant levels ($CO$, $NH_3$, $NO_2$, $O_3$, $PM_{10}$, $PM_{2.5}$, $SO_2$).
- 🔮 **AQI Predictions**: Multi-day futuristic AQI forecasting using trained Machine Learning models.
- ⚡ **Real-time Data Entry**: Input live pollutant concentrations to compute instantaneous CPCB India AQI standards and health advisory notifications.
- 🤖 **On-demand Model Training**: Re-train the Random Forest Regressor directly from the web interface.
- 🎨 **Frosted Glass UI**: Dynamic dashboard with dark glassmorphism aesthetic.

---

## 📁 Repository Structure

```text
AQI_Project/
├── app.py              # Flask server & REST API endpoints
├── ml_model.py         # Data preprocessing, AQI formulas & ML modeling
├── requirements.txt    # Python dependencies
├── .gitignore          # Excluded files (venv, cache, etc.)
├── data/
│   ├── 2024_hourly_data.csv
│   └── aqi_daily.csv
├── model/
│   └── aqi_model.pkl
├── static/             # CSS & JS assets
└── templates/          # HTML views (index.html, dashboard.html)
```

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
cd AQI_Project
```

### 2. Set up Virtual Environment & Install Dependencies
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Launch the Application
```bash
python app.py
```

Open your browser and navigate to **`http://127.0.0.1:5000`**.

---

## 🧪 Tech Stack

- **Backend**: Python 3, Flask, Pandas, NumPy, Scikit-Learn, Joblib
- **Frontend**: HTML5, Vanilla CSS (Glassmorphism design system), JavaScript, Chart.js
- **Model**: Random Forest Regressor for time-series feature engineering and multi-pollutant AQI estimation.
