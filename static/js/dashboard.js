/* ════════════════════════════════════════
   dashboard.js — 5 analysis charts
   Frosted Glass theme colors
════════════════════════════════════════ */

const C = {
  grid:   "rgba(122,173,216,0.18)",
  tick:   "#7a9ab8",
  ttBg:   "rgba(255,255,255,0.92)",
  ttBdr:  "rgba(122,173,216,0.4)",
  ttClr:  "#1a3a5c",
  ttBody: "#4a6a8a",
  font:   { family:"DM Sans" },
};

const inst = {};
function kill(id) { if(inst[id]){ inst[id].destroy(); delete inst[id]; } }

function loadAllCharts() {
  const loading = document.getElementById("dashLoading");
  const content = document.getElementById("dashContent");
  loading.textContent = "Loading your data…";

  fetch("/api/charts")
    .then(r => r.json())
    .then(data => {
      if (!data.success) { loading.textContent = "Error: " + data.message; return; }
      loading.classList.add("hidden");
      content.classList.remove("hidden");
      buildHistorical(data.charts.historical);
      buildMonthly(data.charts.monthly);
      buildDist(data.charts.distribution);
      buildPoll(data.charts.pollutants);
      buildScatter(data.charts.scatter);
    })
    .catch(e => { loading.textContent = "Failed: " + e.message; });
}

/* ── Chart 1: Historical AQI Line ── */
function buildHistorical(d) {
  kill("chartHistorical");
  const ctx = document.getElementById("chartHistorical").getContext("2d");
  const grad = ctx.createLinearGradient(0,0,0,360);
  grad.addColorStop(0, "rgba(90,159,212,0.25)");
  grad.addColorStop(1, "rgba(90,159,212,0.02)");

  inst["chartHistorical"] = new Chart(ctx, {
    type:"line",
    data:{
      labels:d.labels,
      datasets:[
        {
          label:"AQI",
          data:d.values,
          borderColor:"#4a8ec8",
          backgroundColor:grad,
          fill:true, tension:0.4, borderWidth:2.5,
          pointBackgroundColor:d.colors,
          pointBorderColor:"rgba(255,255,255,0.8)",
          pointBorderWidth:1.5,
          pointRadius:4, pointHoverRadius:7,
        },
        {
          label:"Moderate (100)",
          data:Array(d.labels.length).fill(100),
          borderColor:"rgba(255,109,0,0.4)",
          borderDash:[6,4], borderWidth:1.5,
          pointRadius:0, fill:false,
        },
        {
          label:"Poor (200)",
          data:Array(d.labels.length).fill(200),
          borderColor:"rgba(213,0,0,0.4)",
          borderDash:[6,4], borderWidth:1.5,
          pointRadius:0, fill:false,
        }
      ]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      interaction:{mode:"index",intersect:false},
      plugins:{
        legend:{labels:{color:C.tick,font:C.font,boxWidth:14,padding:16}},
        tooltip:{backgroundColor:C.ttBg,borderColor:C.ttBdr,borderWidth:1,
          titleColor:C.ttClr,bodyColor:C.ttBody,titleFont:{...C.font,weight:"600"},
          bodyFont:C.font,padding:10}
      },
      scales:{
        x:{grid:{color:C.grid}, ticks:{color:C.tick,font:{...C.font,size:10},maxTicksLimit:12}},
        y:{grid:{color:C.grid}, ticks:{color:C.tick,font:C.font},
           title:{display:true,text:"AQI Value",color:C.tick,font:C.font}}
      }
    }
  });
}

/* ── Chart 2: Monthly Average Bar ── */
function buildMonthly(d) {
  kill("chartMonthly");
  const ctx = document.getElementById("chartMonthly").getContext("2d");
  const grad = ctx.createLinearGradient(0,0,0,280);
  grad.addColorStop(0, "rgba(74,142,200,0.85)");
  grad.addColorStop(1, "rgba(26,90,154,0.35)");

  inst["chartMonthly"] = new Chart(ctx, {
    type:"bar",
    data:{
      labels:d.labels,
      datasets:[{
        label:"Monthly Avg AQI",
        data:d.values,
        backgroundColor:grad,
        borderColor:"rgba(74,142,200,0.7)",
        borderWidth:1, borderRadius:8,
      }]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{
        legend:{display:false},
        tooltip:{backgroundColor:C.ttBg,borderColor:C.ttBdr,borderWidth:1,
          titleColor:C.ttClr,bodyColor:C.ttBody,titleFont:{...C.font,weight:"600"},bodyFont:C.font,padding:10}
      },
      scales:{
        x:{grid:{color:C.grid},ticks:{color:C.tick,font:{...C.font,size:10}}},
        y:{grid:{color:C.grid},ticks:{color:C.tick,font:C.font}}
      }
    }
  });
}

/* ── Chart 3: Category Donut ── */
function buildDist(d) {
  kill("chartDist");
  const ctx = document.getElementById("chartDist").getContext("2d");
  inst["chartDist"] = new Chart(ctx, {
    type:"doughnut",
    data:{
      labels:d.labels,
      datasets:[{
        data:d.values,
        backgroundColor:d.colors.map(c=>c+"cc"),
        borderColor:"rgba(255,255,255,0.8)",
        borderWidth:2.5, hoverOffset:10,
      }]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      cutout:"58%",
      plugins:{
        legend:{position:"right",
          labels:{color:C.tick,font:{...C.font,size:11},boxWidth:13,padding:12}},
        tooltip:{backgroundColor:C.ttBg,borderColor:C.ttBdr,borderWidth:1,
          titleColor:C.ttClr,bodyColor:C.ttBody,titleFont:{...C.font,weight:"600"},bodyFont:C.font,padding:10}
      }
    }
  });
}

/* ── Chart 4: Pollutant Horizontal Bars ── */
function buildPoll(d) {
  kill("chartPoll");
  const ctx = document.getElementById("chartPoll").getContext("2d");
  inst["chartPoll"] = new Chart(ctx, {
    type:"bar",
    data:{
      labels:d.labels,
      datasets:[{
        label:"Avg (µg/m³)",
        data:d.values,
        backgroundColor:d.colors.map(c=>c+"aa"),
        borderColor:d.colors,
        borderWidth:1.5, borderRadius:6,
      }]
    },
    options:{
      indexAxis:"y",
      responsive:true, maintainAspectRatio:false,
      plugins:{
        legend:{display:false},
        tooltip:{backgroundColor:C.ttBg,borderColor:C.ttBdr,borderWidth:1,
          titleColor:C.ttClr,bodyColor:C.ttBody,titleFont:{...C.font,weight:"600"},bodyFont:C.font,padding:10}
      },
      scales:{
        x:{grid:{color:C.grid},ticks:{color:C.tick,font:C.font}},
        y:{grid:{color:"transparent"},ticks:{color:C.tick,font:{...C.font,size:12}}}
      }
    }
  });
}

/* ── Chart 5: PM2.5 vs AQI Scatter ── */
function buildScatter(d) {
  kill("chartScatter");
  const ctx = document.getElementById("chartScatter").getContext("2d");
  const pts = d.x.map((x,i) => ({x, y:d.y[i]}));
  inst["chartScatter"] = new Chart(ctx, {
    type:"scatter",
    data:{
      datasets:[{
        label:"PM2.5 vs AQI",
        data:pts,
        backgroundColor:d.colors.map(c=>c+"88"),
        borderColor:d.colors,
        borderWidth:1.5, pointRadius:5, pointHoverRadius:8,
      }]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{
        legend:{display:false},
        tooltip:{
          backgroundColor:C.ttBg,borderColor:C.ttBdr,borderWidth:1,
          titleColor:C.ttClr,bodyColor:C.ttBody,
          titleFont:{...C.font,weight:"600"},bodyFont:C.font,padding:10,
          callbacks:{label:ctx=>`PM2.5: ${ctx.parsed.x}  →  AQI: ${ctx.parsed.y}`}
        }
      },
      scales:{
        x:{grid:{color:C.grid},ticks:{color:C.tick,font:C.font},
           title:{display:true,text:"PM2.5 (µg/m³)",color:C.tick,font:C.font}},
        y:{grid:{color:C.grid},ticks:{color:C.tick,font:C.font},
           title:{display:true,text:"AQI Value",color:C.tick,font:C.font}}
      }
    }
  });
}
