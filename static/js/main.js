/* ════════════════════════════════════════
   main.js — AQI Forecast System
   Handles: form submit, train, predict,
            history table, forecast chart
════════════════════════════════════════ */

let forecastChart = null;

document.addEventListener("DOMContentLoaded", function () {
  const d = document.getElementById("entryDate");
  if (d) d.value = new Date().toISOString().split("T")[0];

  const form = document.getElementById("entryForm");
  if (form) form.addEventListener("submit", function(e) {
    e.preventDefault();
    submitEntry(new FormData(form));
  });
});

/* ════════════════════════════════════════
   ADD ENTRY
════════════════════════════════════════ */
function submitEntry(fd) {
  const btn = document.querySelector("#entryForm button[type=submit]");
  const box = document.getElementById("entryMsg");
  btn.disabled = true; btn.textContent = "Saving…";
  showMsg(box, "inf", "Saving entry…");

  fetch("/api/add_entry", { method:"POST", body:fd })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        showMsg(box, "ok",
          `✔ Entry saved! &nbsp;Calculated AQI = <strong style="color:${data.color}">${data.aqi}</strong> (${data.category})`);
        loadHistory();
      } else {
        showMsg(box, "err", "✖ " + data.message);
      }
    })
    .catch(e => showMsg(box, "err", "Network error: " + e.message))
    .finally(() => { btn.disabled=false; btn.textContent="✦ Save Entry"; });
}

/* ════════════════════════════════════════
   TRAIN MODEL
════════════════════════════════════════ */
function trainModel(btn) {
  const box = document.getElementById("trainMsg");
  btn.disabled = true; btn.textContent = "Training…";
  showMsg(box, "inf", "Training Random Forest on your 344 days of data… please wait.");

  fetch("/api/train", { method:"POST" })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        let html = `✔ ${data.message}<br><br>
          <strong>Model Performance:</strong><br>
          R² Score &nbsp;&nbsp;: <strong>${data.r2}</strong> → Accuracy <strong>${data.accuracy}%</strong><br>
          MAE &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: ${data.mae} AQI points average error<br>
          RMSE &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: ${data.rmse}<br>
          Data used : ${data.data_points} days<br><br>
          <strong>Top features the model learned from:</strong><br>`;
        data.feature_importance.slice(0,6).forEach(f => {
          const pct = f.importance;
          html += `${f.feature.padEnd(18)} → ${pct}%<br>`;
        });
        showMsg(box, "ok", html);
      } else {
        showMsg(box, "err", "✖ " + data.message);
      }
    })
    .catch(e => showMsg(box, "err", "Error: " + e.message))
    .finally(() => { btn.disabled=false; btn.textContent="▶ Train Random Forest"; });
}

/* ════════════════════════════════════════
   PREDICT FUTURE
════════════════════════════════════════ */
function runPredict(btn) {
  const days    = document.getElementById("daysSlider").value;
  const loading = document.getElementById("predictLoading");
  const section = document.getElementById("forecastSection");
  btn.disabled  = true;
  loading.classList.remove("hidden");
  section.classList.add("hidden");

  const fd = new FormData();
  fd.append("days", days);

  fetch("/api/predict", { method:"POST", body:fd })
    .then(r => r.json())
    .then(data => {
      loading.classList.add("hidden");
      if (data.success && data.predictions.length > 0) {
        section.classList.remove("hidden");
        drawForecastChart(data.predictions);
        drawForecastCards(data.predictions);
      } else {
        alert(data.message || "Prediction failed. Please train the model first.");
      }
    })
    .catch(e => { loading.classList.add("hidden"); alert("Error: " + e.message); })
    .finally(() => { btn.disabled=false; });
}

/* ── Forecast Bar Chart ── */
function drawForecastChart(preds) {
  const ctx = document.getElementById("forecastChart").getContext("2d");
  if (forecastChart) forecastChart.destroy();
  forecastChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: preds.map(p => p.date_short),
      datasets: [{
        label: "Predicted AQI",
        data:   preds.map(p => p.aqi),
        backgroundColor: preds.map(p => p.color + "99"),
        borderColor:     preds.map(p => p.color),
        borderWidth: 1.5,
        borderRadius: 8,
      }]
    },
    options: {
      responsive:true, maintainAspectRatio:false,
      plugins: {
        legend: { display:false },
        tooltip: {
          backgroundColor: "rgba(255,255,255,0.92)",
          borderColor: "rgba(122,173,216,0.4)", borderWidth: 1,
          titleColor: "#1a3a5c", bodyColor: "#4a6a8a",
          titleFont: { family:"DM Sans", weight:"600", size:12 },
          bodyFont:  { family:"DM Sans", size:11 },
          padding: 10,
          callbacks: {
            afterBody: (items) => {
              const p = preds[items[0].dataIndex];
              return [`Category: ${p.category}`, `PM2.5: ${p.pm25}`, `${p.advice}`];
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color:"rgba(122,173,216,0.15)" },
          ticks:{ color:"#7a9ab8", font:{ family:"DM Sans", size:11 } }
        },
        y: {
          grid: { color:"rgba(122,173,216,0.15)" },
          ticks:{ color:"#7a9ab8", font:{ family:"DM Sans", size:11 } },
          title:{ display:true, text:"AQI Value", color:"#7a9ab8", font:{ family:"DM Sans" } }
        }
      }
    }
  });
}

/* ── Forecast Day Cards ── */
function drawForecastCards(preds) {
  const wrap = document.getElementById("forecastCards");
  wrap.innerHTML = "";
  preds.forEach(p => {
    const div = document.createElement("div");
    div.className = "f-card";
    div.style.borderTopColor = p.color;
    div.title = p.advice;
    div.innerHTML = `
      <div class="f-day">${p.day.slice(0,3).toUpperCase()}</div>
      <div class="f-date">${p.date_short}</div>
      <div class="f-aqi" style="color:${p.color}">${p.aqi}</div>
      <div class="f-cat" style="color:${p.color}">${p.category}</div>`;
    wrap.appendChild(div);
  });
}

/* ════════════════════════════════════════
   HISTORY TABLE
════════════════════════════════════════ */
function loadHistory() {
  const tbody = document.getElementById("historyBody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="10" class="tc">Loading…</td></tr>`;

  fetch("/api/history")
    .then(r => r.json())
    .then(data => {
      if (!data.success || !data.records.length) {
        tbody.innerHTML = `<tr><td colspan="10" class="tc">No entries found.</td></tr>`;
        return;
      }
      tbody.innerHTML = data.records.map(r => `
        <tr>
          <td>${r.date}</td>
          <td><strong style="color:${r.color}">${r.AQI}</strong></td>
          <td>
            <span class="chip"
              style="background:${r.color}18;border-color:${r.color}55;color:${r.color}">
              ${r.cat}
            </span>
          </td>
          <td>${r.PM2_5 ?? "—"}</td>
          <td>${r.PM10  ?? "—"}</td>
          <td>${r.NO2   ?? "—"}</td>
          <td>${r.CO    ?? "—"}</td>
          <td>${r.NH3   ?? "—"}</td>
          <td>${r.O3    ?? "—"}</td>
          <td>${r.SO2   ?? "—"}</td>
        </tr>`).join("");
    })
    .catch(() => {
      tbody.innerHTML = `<tr><td colspan="10" class="tc">Error loading data.</td></tr>`;
    });
}

/* ════════════════════════════════════════
   HELPER
════════════════════════════════════════ */
function showMsg(box, type, html) {
  box.className = "msg " + (type==="ok" ? "msg-ok" : type==="err" ? "msg-err" : "msg-inf");
  box.innerHTML = html;
}
