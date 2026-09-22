"""
================================================
  FILE: ml_model.py
  All ML logic for AQI Forecasting System
  Your data: Date,Time,CO,NH3,NO2,OZONE,PM10,PM2.5,SO2
================================================
"""

import pandas as pd
import numpy as np
import os
import joblib
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings("ignore")

# ── File paths ─────────────────────────────
REAL_CSV   = "data/2024_hourly_data.csv"
DAILY_CSV  = "data/aqi_daily.csv"
MODEL_FILE = "model/aqi_model.pkl"


# ══════════════════════════════════════════
#  AQI FORMULA  (CPCB India)
# ══════════════════════════════════════════

def calc_aqi_from_pm25(pm25):
    if pd.isna(pm25) or pm25 < 0: return np.nan
    if pm25 <= 30:    return pm25 * (50/30)
    elif pm25 <= 60:  return 50  + (pm25-30)  * (50/30)
    elif pm25 <= 90:  return 100 + (pm25-60)  * (50/30)
    elif pm25 <= 120: return 150 + (pm25-90)  * (50/30)
    elif pm25 <= 250: return 200 + (pm25-120) * (100/130)
    else:             return min(500, 300 + (pm25-250) * (100/130))

def aqi_category(aqi):
    if pd.isna(aqi):  return "Unknown",     "#888888"
    if aqi <= 50:     return "Good",         "#00c853"
    elif aqi <= 100:  return "Satisfactory", "#ffd600"
    elif aqi <= 200:  return "Moderate",     "#ff6d00"
    elif aqi <= 300:  return "Poor",         "#d50000"
    elif aqi <= 400:  return "Very Poor",    "#6a1b9a"
    else:             return "Severe",       "#37474f"

def health_advice(aqi):
    if aqi <= 50:    return "Air quality is good. Safe for all outdoor activities."
    elif aqi <= 100: return "Acceptable. Sensitive people should limit long exertion."
    elif aqi <= 200: return "Children & elderly should reduce outdoor exposure."
    elif aqi <= 300: return "Everyone should avoid prolonged outdoor activity."
    elif aqi <= 400: return "Very unhealthy. Stay indoors. Use air purifier."
    else:            return "HAZARDOUS! Avoid all outdoor activity."


# ══════════════════════════════════════════
#  DATA
# ══════════════════════════════════════════

def load_and_aggregate():
    """Read hourly CSV → daily averages → save to aqi_daily.csv"""
    df = pd.read_csv(REAL_CSV)
    df['Date'] = pd.to_datetime(df['Date'])
    daily = df.groupby('Date').agg({
        'CO':'mean','NH3':'mean','NO2':'mean',
        'OZONE':'mean','PM10':'mean','PM2.5':'mean','SO2':'mean'
    }).round(3).reset_index()
    for col in ['CO','NH3','NO2','OZONE','PM10','PM2.5','SO2']:
        daily[col] = daily[col].ffill().bfill()
    daily.rename(columns={'Date':'date','PM2.5':'PM2_5','OZONE':'O3'}, inplace=True)
    daily['AQI'] = daily['PM2_5'].apply(calc_aqi_from_pm25).clip(0,500).round(1)
    daily = daily.sort_values('date').reset_index(drop=True)
    os.makedirs("data", exist_ok=True)
    daily.to_csv(DAILY_CSV, index=False)
    return daily

def load_data():
    """Load daily CSV (aggregate from hourly if needed)"""
    if os.path.exists(DAILY_CSV):
        df = pd.read_csv(DAILY_CSV, parse_dates=['date'])
        if 'PM2.5' in df.columns:
            df.rename(columns={'PM2.5':'PM2_5','OZONE':'O3'}, inplace=True)
        return df.sort_values('date').reset_index(drop=True)
    elif os.path.exists(REAL_CSV):
        return load_and_aggregate()
    else:
        raise FileNotFoundError("No data file found in data/ folder.")

def save_new_entry(row_dict):
    df = load_data()
    new = pd.DataFrame([row_dict])
    new['date'] = pd.to_datetime(new['date'])
    df = pd.concat([df, new], ignore_index=True)
    df.drop_duplicates(subset=['date'], keep='last', inplace=True)
    df.sort_values('date', inplace=True)
    df.to_csv(DAILY_CSV, index=False)

def get_summary_stats():
    df = load_data()
    latest = df.iloc[-1]
    aqi_val = float(latest['AQI'])
    cat, color = aqi_category(aqi_val)
    return {
        "latest_aqi":    round(aqi_val, 1),
        "category":      cat,
        "color":         color,
        "advice":        health_advice(aqi_val),
        "avg_7d":        round(float(df.tail(7)['AQI'].mean()), 1),
        "avg_30d":       round(float(df.tail(30)['AQI'].mean()), 1),
        "total_days":    len(df),
        "latest_date":   str(latest['date'])[:10],
        "pm25":          round(float(latest['PM2_5']), 1),
        "pm10":          round(float(latest['PM10']),  1),
        "no2":           round(float(latest['NO2']),   1),
        "co":            round(float(latest['CO']),    1),
        "model_trained": os.path.exists(MODEL_FILE),
    }


# ══════════════════════════════════════════
#  FEATURE ENGINEERING
# ══════════════════════════════════════════

FEATURE_COLS = [
    'CO','NH3','NO2','O3','PM10','PM2_5','SO2',
    'day_of_week','day_of_year','month',
    'AQI_lag_1','AQI_lag_2','AQI_lag_3','AQI_lag_7',
    'AQI_roll_3','AQI_roll_7',
    'PM2_5_lag1','PM10_lag1','NO2_lag1'
]

def engineer_features(df):
    df = df.copy().sort_values('date').reset_index(drop=True)
    if 'PM2.5' in df.columns:
        df.rename(columns={'PM2.5':'PM2_5','OZONE':'O3'}, inplace=True)
    for col in ['CO','NH3','NO2','O3','PM10','PM2_5','SO2']:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
    df['day_of_week'] = df['date'].dt.dayofweek
    df['day_of_year'] = df['date'].dt.dayofyear
    df['month']       = df['date'].dt.month
    for lag in [1,2,3,7]:
        df[f'AQI_lag_{lag}'] = df['AQI'].shift(lag)
    df['AQI_roll_3'] = df['AQI'].shift(1).rolling(3).mean()
    df['AQI_roll_7'] = df['AQI'].shift(1).rolling(7).mean()
    df['PM2_5_lag1'] = df['PM2_5'].shift(1)
    df['PM10_lag1']  = df['PM10'].shift(1)
    df['NO2_lag1']   = df['NO2'].shift(1)
    df.dropna(inplace=True)
    return df


# ══════════════════════════════════════════
#  TRAIN MODEL
# ══════════════════════════════════════════

def train_model():
    df      = load_data()
    df_feat = engineer_features(df)
    if len(df_feat) < 15:
        return {"success":False,"message":"Need at least 15 days of data."}

    X = df_feat[FEATURE_COLS]
    y = df_feat['AQI']
    split      = int(len(df_feat) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    scaler = StandardScaler()
    Xtr    = scaler.fit_transform(X_train)
    Xte    = scaler.transform(X_test)

    model  = RandomForestRegressor(
        n_estimators=200, max_depth=12,
        min_samples_split=3, random_state=42, n_jobs=-1
    )
    model.fit(Xtr, y_train)

    preds = model.predict(Xte)
    mae   = round(float(mean_absolute_error(y_test, preds)), 2)
    rmse  = round(float(np.sqrt(mean_squared_error(y_test, preds))), 2)
    r2    = round(float(r2_score(y_test, preds)), 4)

    feat_imp = sorted(
        zip(FEATURE_COLS, model.feature_importances_),
        key=lambda x: x[1], reverse=True
    )[:10]

    os.makedirs("model", exist_ok=True)
    joblib.dump({'model':model,'scaler':scaler,'feature_cols':FEATURE_COLS}, MODEL_FILE)

    return {
        "success":     True,
        "message":     f"Model trained on {len(df_feat)} days of real data!",
        "r2":          r2,
        "mae":         mae,
        "rmse":        rmse,
        "accuracy":    round(max(0.0, r2)*100, 2),
        "data_points": len(df_feat),
        "feature_importance": [
            {"feature": f.replace('_',' '), "importance": round(float(v)*100,2)}
            for f,v in feat_imp
        ]
    }


# ══════════════════════════════════════════
#  FUTURE PREDICTION
# ══════════════════════════════════════════

def predict_future(days_ahead=7):
    if not os.path.exists(MODEL_FILE):
        return {"error":"Model not trained. Click Train Model first."}
    bundle = joblib.load(MODEL_FILE)
    model, scaler, feat = bundle['model'], bundle['scaler'], bundle['feature_cols']

    df      = load_data()
    df_pred = engineer_features(df).sort_values('date').reset_index(drop=True)
    if len(df_pred) < 7:
        return {"error":"Need at least 7 days of data."}

    results = []
    for i in range(days_ahead):
        last = df_pred.iloc[-1]
        fd   = pd.Timestamp(last['date']) + timedelta(days=1)
        nr   = {
            'date':        fd,
            'CO':          float(last['CO'])    * np.random.uniform(0.95,1.05),
            'NH3':         float(last['NH3'])   * np.random.uniform(0.95,1.05),
            'NO2':         float(last['NO2'])   * np.random.uniform(0.95,1.05),
            'O3':          float(last['O3'])    * np.random.uniform(0.95,1.05),
            'PM10':        float(last['PM10'])  * np.random.uniform(0.95,1.05),
            'PM2_5':       float(last['PM2_5']) * np.random.uniform(0.95,1.05),
            'SO2':         float(last['SO2'])   * np.random.uniform(0.95,1.05),
            'day_of_week': int(fd.dayofweek),
            'day_of_year': int(fd.dayofyear),
            'month':       int(fd.month),
            'AQI_lag_1':   float(last['AQI']),
            'AQI_lag_2':   float(df_pred.iloc[-2]['AQI']) if len(df_pred)>=2 else float(last['AQI']),
            'AQI_lag_3':   float(df_pred.iloc[-3]['AQI']) if len(df_pred)>=3 else float(last['AQI']),
            'AQI_lag_7':   float(df_pred.iloc[-7]['AQI']) if len(df_pred)>=7 else float(last['AQI']),
            'AQI_roll_3':  float(df_pred['AQI'].tail(3).mean()),
            'AQI_roll_7':  float(df_pred['AQI'].tail(7).mean()),
            'PM2_5_lag1':  float(last['PM2_5']),
            'PM10_lag1':   float(last['PM10']),
            'NO2_lag1':    float(last['NO2']),
        }
        Xn   = pd.DataFrame([nr])[feat]
        pred = float(np.clip(model.predict(scaler.transform(Xn))[0], 0, 500))
        nr['AQI'] = pred
        df_pred = pd.concat([df_pred, pd.DataFrame([nr])], ignore_index=True)
        cat, color = aqi_category(pred)
        results.append({
            "date":       fd.strftime("%Y-%m-%d"),
            "day":        fd.strftime("%A"),
            "date_short": fd.strftime("%b %d"),
            "aqi":        round(pred, 1),
            "category":   cat,
            "color":      color,
            "advice":     health_advice(pred),
            "pm25":       round(float(nr['PM2_5']), 1),
            "pm10":       round(float(nr['PM10']),  1),
        })
    return results


# ══════════════════════════════════════════
#  CHART DATA
# ══════════════════════════════════════════

def get_chart_data():
    df = load_data().sort_values('date')
    if 'PM2.5' in df.columns:
        df.rename(columns={'PM2.5':'PM2_5','OZONE':'O3'}, inplace=True)
    if 'AQI' not in df.columns:
        df['AQI'] = df['PM2_5'].apply(calc_aqi_from_pm25).clip(0,500).round(1)

    hist = df.tail(60)
    chart_historical = {
        "labels": [str(d)[:10] for d in hist['date']],
        "values": [round(float(v),1) for v in hist['AQI']],
        "colors": [aqi_category(v)[1] for v in hist['AQI']],
    }

    df['month_str'] = pd.to_datetime(df['date']).dt.strftime('%b %Y')
    monthly = df.groupby('month_str')['AQI'].mean().tail(12)
    chart_monthly = {
        "labels": list(monthly.index),
        "values": [round(float(v),1) for v in monthly.values],
    }

    last30 = df.tail(30)
    def avg(c): return round(float(last30[c].mean()),1) if c in last30.columns else 0
    chart_pollutants = {
        "labels": ["PM2.5","PM10","NO₂","SO₂","CO","NH₃","O₃"],
        "values": [avg('PM2_5'),avg('PM10'),avg('NO2'),avg('SO2'),avg('CO'),avg('NH3'),avg('O3')],
        "colors": ["#42a5f5","#ef5350","#66bb6a","#ffa726","#ab47bc","#26c6da","#ffca28"],
    }

    cats   = df['AQI'].apply(lambda x: aqi_category(x)[0])
    counts = cats.value_counts().to_dict()
    cmap   = {"Good":"#00c853","Satisfactory":"#ffd600","Moderate":"#ff6d00",
               "Poor":"#d50000","Very Poor":"#6a1b9a","Severe":"#37474f"}
    chart_distribution = {
        "labels": list(counts.keys()),
        "values": list(counts.values()),
        "colors": [cmap.get(k,"#999") for k in counts.keys()],
    }

    sample = df.tail(60)
    chart_scatter = {
        "x": [round(float(v),1) for v in sample['PM2_5']],
        "y": [round(float(v),1) for v in sample['AQI']],
        "colors": [aqi_category(v)[1] for v in sample['AQI']],
    }

    return {
        "historical":   chart_historical,
        "monthly":      chart_monthly,
        "pollutants":   chart_pollutants,
        "distribution": chart_distribution,
        "scatter":      chart_scatter,
    }
