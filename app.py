"""
================================================
  FILE: app.py
  RUN THIS: python app.py
  Then open: http://127.0.0.1:5000
================================================
"""
from flask import Flask, render_template, request, jsonify
import os
from ml_model import (
    load_and_aggregate, load_data, save_new_entry,
    train_model, predict_future, get_chart_data,
    get_summary_stats, calc_aqi_from_pm25, aqi_category,
    DAILY_CSV, MODEL_FILE
)

app = Flask(__name__)

def startup():
    os.makedirs("data",  exist_ok=True)
    os.makedirs("model", exist_ok=True)
    if not os.path.exists(DAILY_CSV):
        print("  Aggregating your hourly data to daily...")
        load_and_aggregate()
        print("  Done!")

@app.route("/")
def home():
    stats = get_summary_stats()
    return render_template("index.html", stats=stats)

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/add_entry", methods=["POST"])
def add_entry():
    try:
        pm25 = float(request.form.get("pm25", 0))
        row  = {
            "date":  request.form.get("date"),
            "CO":    float(request.form.get("co",  0)),
            "NH3":   float(request.form.get("nh3", 0)),
            "NO2":   float(request.form.get("no2", 0)),
            "O3":    float(request.form.get("o3",  0)),
            "PM10":  float(request.form.get("pm10",0)),
            "PM2_5": pm25,
            "SO2":   float(request.form.get("so2", 0)),
        }
        aqi_val    = round(calc_aqi_from_pm25(pm25), 1)
        row["AQI"] = aqi_val
        cat, color = aqi_category(aqi_val)
        save_new_entry(row)
        return jsonify({"success":True,"aqi":aqi_val,"category":cat,"color":color,
                        "message":f"Entry saved! AQI = {aqi_val} ({cat})"})
    except Exception as e:
        return jsonify({"success":False,"message":str(e)})

@app.route("/api/train", methods=["POST"])
def train():
    try:
        return jsonify(train_model())
    except Exception as e:
        return jsonify({"success":False,"message":str(e)})

@app.route("/api/predict", methods=["POST"])
def predict():
    try:
        days  = int(request.form.get("days", 7))
        preds = predict_future(days_ahead=days)
        if isinstance(preds, dict) and "error" in preds:
            return jsonify({"success":False,"message":preds["error"]})
        return jsonify({"success":True,"predictions":preds})
    except Exception as e:
        return jsonify({"success":False,"message":str(e)})

@app.route("/api/charts")
def charts():
    try:
        return jsonify({"success":True,"charts":get_chart_data()})
    except Exception as e:
        return jsonify({"success":False,"message":str(e)})

@app.route("/api/history")
def history():
    try:
        import pandas as pd
        df      = load_data()
        records = df.tail(30).sort_values("date",ascending=False).to_dict("records")
        for r in records:
            r["date"] = str(r["date"])[:10]
            r["AQI"]  = round(float(r["AQI"]),1)
            r["cat"], r["color"] = aqi_category(r["AQI"])
            for col in ["CO","NH3","NO2","O3","PM10","PM2_5","SO2"]:
                if col in r: r[col] = round(float(r[col]),2)
        return jsonify({"success":True,"records":records})
    except Exception as e:
        return jsonify({"success":False,"message":str(e)})

if __name__ == "__main__":
    startup()
    print("\n" + "="*50)
    print("  AQI Forecast System — Frosted Glass Theme")
    print("  Open browser: http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)
