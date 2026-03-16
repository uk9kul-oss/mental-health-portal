const DATA_FILE = "cleaned_mental_illnesses_prevalence.csv";
const DISORDER_COLUMNS = ["schizophrenia", "depressive", "anxiety", "bipolar", "eating"];

const NEWS_ITEMS = [
  { title: "World Health Organization - Mental health", url: "https://www.who.int/health-topics/mental-health" },
  { title: "NIMH - Mental Health Information", url: "https://www.nimh.nih.gov/health" },
  { title: "CDC - Mental Health", url: "https://www.cdc.gov/mentalhealth/index.htm" },
];

const AWARENESS_POINTS = [
  "Mental health conditions are common and treatable.",
  "Early support often improves long-term outcomes.",
  "Regular sleep, movement, and social support can reduce stress burden.",
  "Seeking professional help is a strength, not a weakness.",
  "Community stigma reduction improves care access and recovery.",
];

const FOOD_FOR_THOUGHT = [
  "If your organization tracked stress like a business KPI, what would change?",
  "How do socioeconomic factors amplify mental health inequities?",
  "What would prevention-first mental healthcare look like in schools?",
  "Can digital tools improve access without reducing human connection?",
  "How can workplaces make mental wellbeing measurable and actionable?",
];

const THEME = {
  accent: "#c04b7a",
  text: "#2b1630",
  palette: ["#c04b7a", "#6f5bd3", "#2f9f9a", "#f19a68", "#8f62c9", "#4f79b8"],
  heatmapScale: [
    [0.0, "#fff2f8"],
    [0.5, "#f3b4cf"],
    [1.0, "#8f4b78"],
  ],
};

let allData = [];
let filteredData = [];
let activeMetric = "depressive";
let activeCountry = "";

const els = {
  country: document.getElementById("countrySelect"),
  metric: document.getElementById("metricSelect"),
  yearMin: document.getElementById("yearMin"),
  yearMax: document.getElementById("yearMax"),
  apply: document.getElementById("applyFilters"),
  status: document.getElementById("status"),
  latestYear: document.getElementById("latestYear"),
  latestMetric: document.getElementById("latestMetric"),
  latestTotal: document.getElementById("latestTotal"),
  lrHorizon: document.getElementById("lrHorizon"),
  lrValue: document.getElementById("lrValue"),
  tsHorizon: document.getElementById("tsHorizon"),
  tsValue: document.getElementById("tsValue"),
};

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
  });
});

function randomThought() {
  return FOOD_FOR_THOUGHT[Math.floor(Math.random() * FOOD_FOR_THOUGHT.length)];
}

function parseNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function fmt(value, digits = 3) {
  return value == null ? "-" : Number(value).toFixed(digits);
}

function setStatus(text) {
  els.status.textContent = text;
}

function buildSelect(selectEl, values, selected) {
  selectEl.innerHTML = "";
  values.forEach((value) => {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = value;
    if (value === selected) opt.selected = true;
    selectEl.appendChild(opt);
  });
}

function renderTable(tableId, rows, columns) {
  const table = document.getElementById(tableId);
  if (!rows.length) {
    table.innerHTML = "<tr><td>No rows</td></tr>";
    return;
  }
  const cols = columns || Object.keys(rows[0]);
  const head = `<thead><tr>${cols.map((c) => `<th>${c}</th>`).join("")}</tr></thead>`;
  const bodyRows = rows
    .map((row) => `<tr>${cols.map((c) => `<td>${row[c] ?? ""}</td>`).join("")}</tr>`)
    .join("");
  table.innerHTML = `${head}<tbody>${bodyRows}</tbody>`;
}

function filterData() {
  activeCountry = els.country.value;
  activeMetric = els.metric.value;
  const minYear = Number(els.yearMin.value);
  const maxYear = Number(els.yearMax.value);
  filteredData = allData
    .filter((row) => row.Entity === activeCountry && row.Year >= minYear && row.Year <= maxYear)
    .sort((a, b) => a.Year - b.Year);

  if (!filteredData.length) {
    setStatus("No data found for selected filters.");
    return;
  }
  setStatus(`Showing ${filteredData.length} rows for ${activeCountry}.`);
  renderAll();
}

function buildLinearPrediction(rows, metric, horizon) {
  const pairs = rows
    .map((r) => ({ x: r.Year, y: r[metric] }))
    .filter((r) => r.y != null);

  const n = pairs.length;
  const sumX = pairs.reduce((s, p) => s + p.x, 0);
  const sumY = pairs.reduce((s, p) => s + p.y, 0);
  const sumXY = pairs.reduce((s, p) => s + p.x * p.y, 0);
  const sumXX = pairs.reduce((s, p) => s + p.x * p.x, 0);

  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX || 1);
  const intercept = (sumY - slope * sumX) / (n || 1);

  const maxYear = Math.max(...pairs.map((p) => p.x));
  return Array.from({ length: horizon }, (_, i) => {
    const year = maxYear + i + 1;
    return { Year: year, predicted: intercept + slope * year };
  });
}

function buildTsForecast(rows, metric, horizon) {
  const values = rows.map((r) => r[metric]).filter((v) => v != null);
  if (!values.length) return [];

  const alpha = 0.35;
  let level = values[0];
  let trend = values.length > 1 ? values[1] - values[0] : 0;

  for (let i = 1; i < values.length; i += 1) {
    const value = values[i];
    const prevLevel = level;
    level = alpha * value + (1 - alpha) * (level + trend);
    trend = alpha * (level - prevLevel) + (1 - alpha) * trend;
  }

  const maxYear = Math.max(...rows.map((r) => r.Year));
  return Array.from({ length: horizon }, (_, i) => {
    const step = i + 1;
    return { Year: maxYear + step, forecast: level + step * trend };
  });
}

function renderDashboard() {
  const latest = filteredData[filteredData.length - 1];
  els.latestYear.textContent = latest?.Year ?? "-";
  els.latestMetric.textContent = fmt(latest?.[activeMetric]);
  els.latestTotal.textContent = fmt(latest?.total_burden);

  Plotly.newPlot("mainTrend", [{
    x: filteredData.map((r) => r.Year),
    y: filteredData.map((r) => r[activeMetric]),
    mode: "lines+markers",
    line: { color: THEME.accent, width: 3 },
    name: activeMetric,
  }], {
    title: `${activeCountry}: ${activeMetric} over time`,
    paper_bgcolor: "#fff9fc",
    plot_bgcolor: "#fff",
    font: { color: THEME.text },
  }, { responsive: true });

  const traces = DISORDER_COLUMNS.map((metric, i) => ({
    x: filteredData.map((r) => r.Year),
    y: filteredData.map((r) => r[metric]),
    mode: "lines",
    name: metric,
    line: { color: THEME.palette[i] },
  }));

  Plotly.newPlot("allDisorders", traces, {
    title: "All disorders trend",
    paper_bgcolor: "#fff9fc",
    plot_bgcolor: "#fff",
    font: { color: THEME.text },
  }, { responsive: true });

  const pieData = DISORDER_COLUMNS.map((m) => latest?.[m] ?? 0);
  Plotly.newPlot("composition", [{
    type: "pie",
    labels: DISORDER_COLUMNS,
    values: pieData,
    hole: 0.45,
    marker: { colors: THEME.palette },
  }], {
    title: `${latest?.Year ?? "Latest"} composition`,
    paper_bgcolor: "#fff9fc",
    font: { color: THEME.text },
  }, { responsive: true });

  const z = DISORDER_COLUMNS.map((metric) => filteredData.map((row) => row[metric]));
  Plotly.newPlot("heatmap", [{
    type: "heatmap",
    x: filteredData.map((r) => r.Year),
    y: DISORDER_COLUMNS,
    z,
    colorscale: THEME.heatmapScale,
  }], {
    title: "Disorder intensity heatmap by year",
    paper_bgcolor: "#fff9fc",
    plot_bgcolor: "#fff",
    font: { color: THEME.text },
  }, { responsive: true });

  renderTable(
    "previewTable",
    filteredData.slice(0, 20).map((row) => ({
      Entity: row.Entity,
      Code: row.Code,
      Year: row.Year,
      schizophrenia: fmt(row.schizophrenia),
      depressive: fmt(row.depressive),
      anxiety: fmt(row.anxiety),
      bipolar: fmt(row.bipolar),
      eating: fmt(row.eating),
      total_burden: fmt(row.total_burden),
    }))
  );
}

function renderPrediction() {
  const horizon = Number(els.lrHorizon.value);
  els.lrValue.textContent = String(horizon);

  const pred = buildLinearPrediction(filteredData, activeMetric, horizon);
  const historical = {
    x: filteredData.map((r) => r.Year),
    y: filteredData.map((r) => r[activeMetric]),
    mode: "lines+markers",
    name: "Historical",
    line: { color: THEME.accent, width: 3 },
  };

  const predicted = {
    x: pred.map((r) => r.Year),
    y: pred.map((r) => r.predicted),
    mode: "lines+markers",
    name: "Predicted",
    line: { color: THEME.palette[1], dash: "dash" },
  };

  Plotly.newPlot("predictionChart", [historical, predicted], {
    title: "Linear Regression Prediction",
    paper_bgcolor: "#fff9fc",
    plot_bgcolor: "#fff",
    font: { color: THEME.text },
  }, { responsive: true });

  renderTable("predictionTable", pred.map((r) => ({ Year: r.Year, predicted: fmt(r.predicted) })));
}

function renderTimeSeries() {
  const horizon = Number(els.tsHorizon.value);
  els.tsValue.textContent = String(horizon);

  const rolling = filteredData.map((row, index) => {
    const start = Math.max(0, index - 2);
    const slice = filteredData.slice(start, index + 1).map((r) => r[activeMetric]);
    const avg = slice.reduce((s, v) => s + v, 0) / slice.length;
    return { Year: row.Year, value: avg };
  });

  const yoy = filteredData.map((row, index) => {
    if (index === 0) return { Year: row.Year, metric: fmt(row[activeMetric]), yoy: "-" };
    const prev = filteredData[index - 1][activeMetric];
    const current = row[activeMetric];
    const change = prev === 0 ? null : ((current - prev) / prev) * 100;
    return { Year: row.Year, metric: fmt(current), yoy: fmt(change, 2) };
  });

  const forecast = buildTsForecast(filteredData, activeMetric, horizon);

  Plotly.newPlot("timeSeriesChart", [
    {
      x: filteredData.map((r) => r.Year),
      y: filteredData.map((r) => r[activeMetric]),
      mode: "lines+markers",
      name: "Historical",
      line: { color: THEME.accent, width: 3 },
    },
    {
      x: rolling.map((r) => r.Year),
      y: rolling.map((r) => r.value),
      mode: "lines",
      name: "Rolling 3y",
      line: { color: THEME.palette[2] },
    },
    {
      x: forecast.map((r) => r.Year),
      y: forecast.map((r) => r.forecast),
      mode: "lines+markers",
      name: "Forecast",
      line: { color: THEME.palette[1], dash: "dot" },
    },
  ], {
    title: "Historical trend + rolling mean + forecast",
    paper_bgcolor: "#fff9fc",
    plot_bgcolor: "#fff",
    font: { color: THEME.text },
  }, { responsive: true });

  renderTable("yoyTable", yoy, ["Year", "metric", "yoy"]);
}

function renderInsights() {
  const newsList = document.getElementById("newsList");
  newsList.innerHTML = NEWS_ITEMS.map((n) => `<li><a href="${n.url}" target="_blank" rel="noreferrer">${n.title}</a></li>`).join("");

  const awarenessList = document.getElementById("awarenessList");
  awarenessList.innerHTML = AWARENESS_POINTS.map((p) => `<li>${p}</li>`).join("");

  document.getElementById("thoughtText").textContent = randomThought();
}

function downloadBlob(filename, mimeType, content) {
  const blob = new Blob([content], { type: mimeType });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

function setupExports() {
  document.getElementById("downloadCsv").addEventListener("click", () => {
    const csv = Papa.unparse(filteredData);
    downloadBlob(`${activeCountry}_${activeMetric}_report.csv`, "text/csv", csv);
  });

  document.getElementById("downloadExcel").addEventListener("click", () => {
    const ws = XLSX.utils.json_to_sheet(filteredData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "report");
    const output = XLSX.write(wb, { bookType: "xlsx", type: "array" });
    downloadBlob(`${activeCountry}_${activeMetric}_report.xlsx`, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", output);
  });

  document.getElementById("downloadPdf").addEventListener("click", () => {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    doc.setFontSize(14);
    doc.text("Mental Health Report", 14, 14);
    doc.setFontSize(10);
    doc.text(`Country: ${activeCountry}`, 14, 24);
    doc.text(`Metric: ${activeMetric}`, 14, 30);
    doc.text(`Rows: ${filteredData.length}`, 14, 36);

    const rows = filteredData.slice(0, 20).map((r) => [
      r.Entity,
      r.Code,
      r.Year,
      fmt(r[activeMetric]),
      fmt(r.total_burden),
    ]);

    doc.autoTable({
      startY: 42,
      head: [["Entity", "Code", "Year", activeMetric, "total_burden"]],
      body: rows,
    });
    doc.save(`${activeCountry}_${activeMetric}_report.pdf`);
  });

  document.getElementById("downloadJpeg").addEventListener("click", () => {
    const chart = document.getElementById("mainTrend");
    Plotly.downloadImage(chart, { format: "jpeg", filename: "image", width: 1200, height: 700 });
  });
}

function renderAll() {
  if (!filteredData.length) return;
  renderDashboard();
  renderPrediction();
  renderTimeSeries();
}

async function loadData() {
  setStatus("Loading cleaned CSV...");
  const res = await fetch(DATA_FILE);
  if (!res.ok) {
    throw new Error(`Could not load ${DATA_FILE}. Serve this folder with a local web server.`);
  }

  const csvText = await res.text();
  const parsed = Papa.parse(csvText, { header: true, skipEmptyLines: true });
  allData = parsed.data
    .map((r) => ({
      Entity: String(r.Entity || "").trim(),
      Code: String(r.Code || "").trim(),
      Year: parseNumber(r.Year),
      schizophrenia: parseNumber(r.schizophrenia),
      depressive: parseNumber(r.depressive),
      anxiety: parseNumber(r.anxiety),
      bipolar: parseNumber(r.bipolar),
      eating: parseNumber(r.eating),
      total_burden: parseNumber(r.total_burden),
    }))
    .filter((r) => r.Entity && r.Year != null && DISORDER_COLUMNS.every((c) => r[c] != null));

  const countries = [...new Set(allData.map((r) => r.Entity))].sort((a, b) => a.localeCompare(b));
  const years = allData.map((r) => r.Year);
  const minYear = Math.min(...years);
  const maxYear = Math.max(...years);

  activeCountry = countries[0];
  buildSelect(els.country, countries, activeCountry);
  buildSelect(els.metric, [...DISORDER_COLUMNS, "total_burden"], activeMetric);

  els.yearMin.value = String(minYear);
  els.yearMax.value = String(maxYear);
  els.yearMin.min = String(minYear);
  els.yearMin.max = String(maxYear);
  els.yearMax.min = String(minYear);
  els.yearMax.max = String(maxYear);

  els.apply.addEventListener("click", filterData);
  els.metric.addEventListener("change", filterData);
  els.country.addEventListener("change", filterData);
  els.lrHorizon.addEventListener("input", renderPrediction);
  els.tsHorizon.addEventListener("input", renderTimeSeries);
  document.getElementById("newThought").addEventListener("click", () => {
    document.getElementById("thoughtText").textContent = randomThought();
  });

  renderInsights();
  setupExports();
  filterData();
}

loadData().catch((err) => {
  setStatus(err.message);
});
