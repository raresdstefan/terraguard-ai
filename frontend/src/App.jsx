import { useState, useEffect, useRef } from "react";

const SOIL_PROFILES = [
  { id: 1, name: "Field Alpha", zone: "North Quadrant", lat: "44.2°N", lon: "26.1°E" },
  { id: 2, name: "Field Beta",  zone: "South Quadrant", lat: "44.1°N", lon: "26.3°E" },
  { id: 3, name: "Greenhouse 1", zone: "Indoor Zone", lat: "44.2°N", lon: "26.2°E" },
];

const COLORS = {
  moss:    "#4a6741",
  sage:    "#7a9e6e",
  clay:    "#b87d4b",
  sand:    "#d4b896",
  earth:   "#3d2e1e",
  mist:    "#e8ede4",
  leaf:    "#c8dfc0",
  amber:   "#d4882a",
  danger:  "#b84a3a",
  sky:     "#7ab0c8",
};

function generateReadings() {
  return {
    humidity: +(45 + Math.random() * 40).toFixed(1),
    light:    +(200 + Math.random() * 800).toFixed(0),
    ph:       +(5.5 + Math.random() * 2.5).toFixed(2),
    temp:     +(14 + Math.random() * 16).toFixed(1),
    nitrogen: +(20 + Math.random() * 60).toFixed(0),
    moisture: +(30 + Math.random() * 50).toFixed(1),
  };
}

function classifyHealth(r) {
  let score = 0;
  if (r.humidity >= 50 && r.humidity <= 70) score += 2;
  else if (r.humidity >= 35 && r.humidity < 85) score += 1;
  if (r.ph >= 6.0 && r.ph <= 7.0) score += 2;
  else if (r.ph >= 5.5 && r.ph < 7.5) score += 1;
  if (r.light >= 400 && r.light <= 800) score += 1;
  if (r.nitrogen >= 40) score += 1;
  if (r.moisture >= 40 && r.moisture <= 65) score += 2;
  return score >= 7 ? "Optimal" : score >= 4 ? "Moderate" : "Poor";
}

function getHealthColor(status) {
  if (status === "Optimal")  return COLORS.moss;
  if (status === "Moderate") return COLORS.amber;
  return COLORS.danger;
}

function getAIInsight(r, status) {
  const insights = [];
  if (r.ph < 6.0)  insights.push("pH is below optimal range — consider lime amendment to raise acidity.");
  if (r.ph > 7.2)  insights.push("pH is alkaline — sulphur-based treatment may improve nutrient absorption.");
  if (r.humidity < 40) insights.push("Humidity is low — increase irrigation frequency.");
  if (r.humidity > 78) insights.push("High humidity detected — risk of fungal growth, improve drainage.");
  if (r.nitrogen < 30) insights.push("Nitrogen deficiency likely — apply balanced fertiliser.");
  if (r.moisture < 35)  insights.push("Soil moisture is critically low — immediate irrigation recommended.");
  if (r.light < 300)   insights.push("Light levels are suboptimal — check for canopy shading.");
  if (insights.length === 0) {
    insights.push("All sensor readings are within optimal ranges. Continue current maintenance regime.");
  }
  return insights;
}

function RadialGauge({ value, min, max, label, unit, color, size = 100 }) {
  const pct = Math.min(1, Math.max(0, (value - min) / (max - min)));
  const r = 38, cx = 50, cy = 54;
  const startAngle = -210, sweepAngle = 240;
  const angle = startAngle + sweepAngle * pct;
  const toRad = d => (d * Math.PI) / 180;
  const arcX = (a, radius) => cx + radius * Math.cos(toRad(a));
  const arcY = (a, radius) => cy + radius * Math.sin(toRad(a));
  const describeArc = (start, end, radius) => {
    const s = { x: arcX(start, radius), y: arcY(start, radius) };
    const e = { x: arcX(end, radius),   y: arcY(end, radius) };
    const large = end - start > 180 ? 1 : 0;
    return `M ${s.x} ${s.y} A ${radius} ${radius} 0 ${large} 1 ${e.x} ${e.y}`;
  };
  return (
    <svg viewBox="0 0 100 90" width={size} height={size * 0.9} style={{ overflow: "visible" }}>
      <path d={describeArc(-210, 30, r)} fill="none" stroke="#e0ddd8" strokeWidth="5" strokeLinecap="round" />
      <path d={describeArc(-210, angle, r)} fill="none" stroke={color} strokeWidth="5" strokeLinecap="round" />
      <line
        x1={cx} y1={cy}
        x2={cx + (r - 12) * Math.cos(toRad(angle))}
        y2={cy + (r - 12) * Math.sin(toRad(angle))}
        stroke={color} strokeWidth="1.5" strokeLinecap="round"
      />
      <circle cx={cx} cy={cy} r="3" fill={color} />
      <text x={cx} y={cy + 18} textAnchor="middle" style={{ fontSize: 13, fontWeight: 600, fill: COLORS.earth, fontFamily: "inherit" }}>
        {value}{unit}
      </text>
      <text x={cx} y={cy + 28} textAnchor="middle" style={{ fontSize: 8, fill: "#8a7e72", fontFamily: "inherit" }}>
        {label}
      </text>
    </svg>
  );
}

function SparkLine({ history, color }) {
  if (!history || history.length < 2) return null;
  const w = 120, h = 32, pad = 4;
  const min = Math.min(...history);
  const max = Math.max(...history);
  const range = max - min || 1;
  const pts = history.map((v, i) => {
    const x = pad + (i / (history.length - 1)) * (w - pad * 2);
    const y = h - pad - ((v - min) / range) * (h - pad * 2);
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} width={w} height={h} style={{ display: "block" }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.7" />
    </svg>
  );
}

function SensorCard({ label, value, unit, min, max, color, icon, history }) {
  const pct = Math.round(((value - min) / (max - min)) * 100);
  return (
    <div style={{
      background: "#fff",
      borderRadius: 14,
      padding: "16px 18px",
      border: `1px solid #e4e0db`,
      display: "flex",
      flexDirection: "column",
      gap: 6,
      position: "relative",
      overflow: "hidden",
    }}>
      <div style={{ position: "absolute", top: 0, left: 0, width: `${pct}%`, height: 3, background: color, borderRadius: "3px 0 0 0", transition: "width 0.8s ease" }} />
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontSize: 11, color: "#9a8f84", letterSpacing: "0.08em", textTransform: "uppercase", fontWeight: 500 }}>{label}</span>
        <span style={{ fontSize: 10, background: color + "22", color, borderRadius: 6, padding: "2px 7px", fontWeight: 600 }}>{icon}</span>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
        <span style={{ fontSize: 26, fontWeight: 700, color: COLORS.earth, fontFamily: "'Playfair Display', serif", lineHeight: 1 }}>{value}</span>
        <span style={{ fontSize: 12, color: "#9a8f84" }}>{unit}</span>
      </div>
      <SparkLine history={history} color={color} />
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, color: "#bbb", marginTop: 2 }}>
        <span>{min}{unit}</span><span>{max}{unit}</span>
      </div>
    </div>
  );
}

function HealthBadge({ status }) {
  const c = getHealthColor(status);
  const dot = status === "Optimal" ? "✦" : status === "Moderate" ? "◆" : "▲";
  return (
    <div style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      background: c + "18", border: `1px solid ${c}44`,
      borderRadius: 20, padding: "5px 14px",
      fontSize: 12, fontWeight: 600, color: c,
      letterSpacing: "0.04em"
    }}>
      <span style={{ fontSize: 9 }}>{dot}</span>
      {status}
    </div>
  );
}

function AIPanel({ readings, status }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function runAnalysis() {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const prompt = `You are TerraGuard AI, an expert soil health analyst. Analyze the following sensor readings and provide a concise assessment (3-4 sentences max). Be specific about what the numbers mean for crop health.

Sensor Data:
- Humidity: ${readings.humidity}%
- Light: ${readings.light} lux
- pH: ${readings.ph}
- Temperature: ${readings.temp}°C
- Nitrogen: ${readings.nitrogen} mg/kg
- Soil Moisture: ${readings.moisture}%
- Overall Status: ${status}

Provide: 1) A one-sentence health summary. 2) The single most urgent action to take. 3) One positive observation. Keep it practical and farmer-friendly.`;

      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          messages: [{ role: "user", content: prompt }],
        }),
      });
      const data = await res.json();
      const text = data.content?.map(b => b.text || "").join("") || "No response.";
      setResult(text);
    } catch (e) {
      setError("Analysis unavailable. Check connection.");
    }
    setLoading(false);
  }

  return (
    <div style={{
      background: "linear-gradient(135deg, #f5f1eb 0%, #eef4e8 100%)",
      borderRadius: 16, padding: "22px 24px",
      border: "1px solid #ddd8d0",
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: COLORS.moss, display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 18
          }}>🌱</div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.earth }}>AI Field Analysis</div>
            <div style={{ fontSize: 11, color: "#9a8f84" }}>Powered by Claude</div>
          </div>
        </div>
        <button
          onClick={runAnalysis}
          disabled={loading}
          style={{
            background: loading ? "#c8c4be" : COLORS.moss,
            color: "#fff", border: "none", borderRadius: 10,
            padding: "8px 18px", fontSize: 12, fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
            transition: "background 0.2s",
            letterSpacing: "0.03em",
          }}
        >
          {loading ? "Analysing…" : "Run Analysis"}
        </button>
      </div>

      {!result && !loading && !error && (
        <div style={{ color: "#a09488", fontSize: 13, fontStyle: "italic", padding: "10px 0" }}>
          Press "Run Analysis" to get an AI-powered assessment of your field's soil health based on current sensor readings.
        </div>
      )}
      {loading && (
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 0" }}>
          <div style={{
            width: 18, height: 18, borderRadius: "50%",
            border: `2px solid ${COLORS.sage}`,
            borderTopColor: "transparent",
            animation: "spin 0.8s linear infinite",
          }} />
          <span style={{ fontSize: 13, color: COLORS.moss }}>Interpreting sensor data…</span>
        </div>
      )}
      {error && <div style={{ color: COLORS.danger, fontSize: 13, padding: "8px 0" }}>{error}</div>}
      {result && (
        <div style={{
          fontSize: 13.5, lineHeight: 1.75, color: "#3d2e1e",
          borderTop: "1px solid #ddd8d0", paddingTop: 14, marginTop: 4,
          whiteSpace: "pre-wrap",
        }}>
          {result}
        </div>
      )}

      <div style={{ marginTop: 16, borderTop: "1px solid #ddd8d0", paddingTop: 14 }}>
        <div style={{ fontSize: 11, color: "#9a8f84", marginBottom: 8, fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase" }}>Quick Diagnostics</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {getAIInsight(readings, status).map((tip, i) => (
            <div key={i} style={{ display: "flex", gap: 8, fontSize: 12.5, color: "#5a4e44" }}>
              <span style={{ color: COLORS.clay, marginTop: 1 }}>›</span>
              <span>{tip}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Sidebar({ profiles, activeId, onSelect, readings }) {
  return (
    <div style={{
      width: 220, flexShrink: 0,
      background: COLORS.earth,
      borderRadius: 18, padding: "24px 16px",
      display: "flex", flexDirection: "column", gap: 8,
      color: "#fff",
    }}>
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 11, color: "#9a8e84", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 4 }}>TerraGuard</div>
        <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "'Playfair Display', serif", lineHeight: 1.2 }}>Soil<br/>Intelligence</div>
      </div>

      <div style={{ fontSize: 11, color: "#7a6e64", letterSpacing: "0.08em", textTransform: "uppercase", marginTop: 8, marginBottom: 4 }}>Fields</div>
      {profiles.map(p => (
        <button key={p.id} onClick={() => onSelect(p.id)} style={{
          background: activeId === p.id ? COLORS.moss + "cc" : "transparent",
          border: "none", borderRadius: 10, padding: "10px 12px",
          color: activeId === p.id ? "#fff" : "#c4b9ae",
          textAlign: "left", cursor: "pointer", transition: "all 0.2s",
          fontSize: 13,
        }}>
          <div style={{ fontWeight: 600 }}>{p.name}</div>
          <div style={{ fontSize: 10, opacity: 0.7, marginTop: 2 }}>{p.zone}</div>
        </button>
      ))}

      <div style={{ marginTop: "auto", paddingTop: 20, borderTop: "1px solid #5a4e44" }}>
        <div style={{ fontSize: 11, color: "#7a6e64", marginBottom: 8 }}>System Status</div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#6fcf7a", display: "inline-block" }} />
          <span style={{ color: "#c4b9ae" }}>Sensors Online</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, marginTop: 4 }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#f0c040", display: "inline-block" }} />
          <span style={{ color: "#c4b9ae" }}>RabbitMQ Connected</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, marginTop: 4 }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#6fcf7a", display: "inline-block" }} />
          <span style={{ color: "#c4b9ae" }}>ML Model Active</span>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [activeField, setActiveField] = useState(1);
  const [readings, setReadings] = useState(generateReadings());
  const [history, setHistory] = useState(() => {
    const h = {};
    ["humidity","light","ph","temp","nitrogen","moisture"].forEach(k => {
      h[k] = Array.from({ length: 12 }, () => generateReadings()[k]);
    });
    return h;
  });
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [refreshing, setRefreshing] = useState(false);

  const status = classifyHealth(readings);

  function refresh() {
    setRefreshing(true);
    setTimeout(() => {
      const r = generateReadings();
      setReadings(r);
      setHistory(prev => {
        const next = {};
        Object.keys(prev).forEach(k => next[k] = [...prev[k].slice(-11), r[k]]);
        return next;
      });
      setLastUpdated(new Date());
      setRefreshing(false);
    }, 600);
  }

  useEffect(() => {
    const t = setInterval(refresh, 15000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const r = generateReadings();
    setReadings(r);
    setHistory(() => {
      const h = {};
      ["humidity","light","ph","temp","nitrogen","moisture"].forEach(k => {
        h[k] = Array.from({ length: 12 }, () => generateReadings()[k]);
      });
      return h;
    });
  }, [activeField]);

  const activeProfile = SOIL_PROFILES.find(p => p.id === activeField);

  const sensors = [
    { key: "humidity",  label: "Humidity",      unit: "%",       min: 0,   max: 100, color: COLORS.sky,  icon: "💧" },
    { key: "light",     label: "Light",          unit: " lux",   min: 0,   max: 1200,color: COLORS.amber,icon: "☀" },
    { key: "ph",        label: "pH Level",       unit: "",        min: 4,   max: 9,   color: COLORS.sage, icon: "⚗" },
    { key: "temp",      label: "Temperature",    unit: "°C",      min: 5,   max: 35,  color: COLORS.clay, icon: "🌡" },
    { key: "nitrogen",  label: "Nitrogen",       unit: " mg/kg",  min: 0,   max: 100, color: COLORS.moss, icon: "🌿" },
    { key: "moisture",  label: "Soil Moisture",  unit: "%",       min: 0,   max: 100, color: COLORS.earth + "bb",icon: "🪨" },
  ];

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@300;400;500;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'DM Sans', sans-serif; background: #f0ece4; color: ${COLORS.earth}; min-height: 100vh; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
        .sensor-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; animation: fadeIn 0.5s ease; }
        @media (max-width: 900px) { .sensor-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 600px) { .sensor-grid { grid-template-columns: 1fr; } }
      `}</style>

      <div style={{ display: "flex", minHeight: "100vh", padding: "20px", gap: 18 }}>
        <Sidebar profiles={SOIL_PROFILES} activeId={activeField} onSelect={setActiveField} readings={readings} />

        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 18, minWidth: 0 }}>

          {/* Header */}
          <div style={{
            background: "#fff", borderRadius: 16, padding: "18px 24px",
            border: "1px solid #e4e0db",
            display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12,
          }}>
            <div>
              <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "'Playfair Display', serif", color: COLORS.earth }}>
                {activeProfile.name}
              </div>
              <div style={{ fontSize: 12, color: "#9a8f84", marginTop: 2 }}>
                {activeProfile.zone} · {activeProfile.lat}, {activeProfile.lon}
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
              <HealthBadge status={status} />
              <div style={{ fontSize: 11, color: "#b0a89e" }}>
                Updated {lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
              </div>
              <button
                onClick={refresh}
                disabled={refreshing}
                style={{
                  background: refreshing ? "#e4e0db" : "#f0ece4",
                  border: "1px solid #ddd8d0", borderRadius: 8,
                  padding: "7px 14px", fontSize: 12, cursor: refreshing ? "not-allowed" : "pointer",
                  color: COLORS.earth, fontWeight: 500, transition: "all 0.2s",
                }}
              >
                {refreshing ? "Refreshing…" : "↻ Refresh"}
              </button>
            </div>
          </div>

          {/* Gauge Row */}
          <div style={{
            background: "#fff", borderRadius: 16, padding: "20px 24px",
            border: "1px solid #e4e0db",
          }}>
            <div style={{ fontSize: 11, color: "#9a8f84", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 14, fontWeight: 600 }}>
              Live Sensor Readings
            </div>
            <div style={{ display: "flex", gap: 0, justifyContent: "space-around", flexWrap: "wrap" }}>
              {sensors.map(s => (
                <RadialGauge
                  key={s.key}
                  value={readings[s.key]}
                  min={s.min} max={s.max}
                  label={s.label} unit={s.unit}
                  color={s.color} size={110}
                />
              ))}
            </div>
          </div>

          {/* Sensor Cards + AI Panel */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: 18 }}>
            <div className="sensor-grid">
              {sensors.map(s => (
                <SensorCard
                  key={s.key}
                  label={s.label}
                  value={readings[s.key]}
                  unit={s.unit}
                  min={s.min} max={s.max}
                  color={s.color}
                  icon={s.icon}
                  history={history[s.key]}
                />
              ))}
            </div>
            <AIPanel readings={readings} status={status} />
          </div>

          {/* Footer */}
          <div style={{ fontSize: 11, color: "#b0a89e", textAlign: "center", paddingBottom: 8 }}>
            TerraGuard AI · POC Build · Sensor data is simulated · RabbitMQ + Docker
          </div>
        </div>
      </div>
    </>
  );
}
