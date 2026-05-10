import { useState, useEffect, useCallback } from "react";

const API_BASE = "http://localhost:8000";

const COLORS = {
  moss:   "#4a6741",
  sage:   "#7a9e6e",
  clay:   "#b87d4b",
  earth:  "#3d2e1e",
  amber:  "#c47f1a",
  danger: "#b84a3a",
  sky:    "#5a96b8",
  mist:   "#f4f1ec",
  border: "#e4dfd8",
};

function soilQualityColor(quality) {
  if (!quality) return COLORS.sage;
  const q = quality.toLowerCase();
  if (q.includes("high") || q.includes("excellent") || q.includes("good")) return COLORS.moss;
  if (q.includes("medium") || q.includes("moderate") || q.includes("average")) return COLORS.amber;
  return COLORS.danger;
}

function RadialGauge({ value, min, max, label, unit, color, size = 108 }) {
  const pct   = Math.min(1, Math.max(0, (value - min) / (max - min)));
  const R     = 36, cx = 50, cy = 52;
  const start = -210, sweep = 240;
  const angle = start + sweep * pct;
  const rad   = d => (d * Math.PI) / 180;
  const pt    = (a, r) => [cx + r * Math.cos(rad(a)), cy + r * Math.sin(rad(a))];
  const arc   = (a1, a2, r) => {
    const [sx, sy] = pt(a1, r), [ex, ey] = pt(a2, r);
    return `M ${sx} ${sy} A ${r} ${r} 0 ${a2 - a1 > 180 ? 1 : 0} 1 ${ex} ${ey}`;
  };
  const [nx, ny] = pt(angle, R - 10);
  return (
    <svg viewBox="0 0 100 86" width={size} height={size * 0.86} style={{ overflow: "visible" }}>
      <path d={arc(-210, 30, R)} fill="none" stroke="#e8e3dc" strokeWidth="5" strokeLinecap="round" />
      <path d={arc(-210, angle, R)} fill="none" stroke={color} strokeWidth="5" strokeLinecap="round" />
      <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      <circle cx={cx} cy={cy} r="3" fill={color} />
      <text x={cx} y={cy + 17} textAnchor="middle"
        style={{ fontSize: 12, fontWeight: 700, fill: COLORS.earth, fontFamily: "inherit" }}>
        {value}{unit}
      </text>
      <text x={cx} y={cy + 27} textAnchor="middle"
        style={{ fontSize: 7.5, fill: "#9a8f84", fontFamily: "inherit" }}>
        {label}
      </text>
    </svg>
  );
}

function Spark({ history, color }) {
  if (!history || history.length < 2) return <div style={{ height: 28 }} />;
  const W = 110, H = 28, P = 3;
  const lo = Math.min(...history), hi = Math.max(...history);
  const range = hi - lo || 1;
  const pts = history.map((v, i) => {
    const x = P + (i / (history.length - 1)) * (W - P * 2);
    const y = H - P - ((v - lo) / range) * (H - P * 2);
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5"
        strokeLinecap="round" strokeLinejoin="round" opacity="0.65" />
    </svg>
  );
}

function SensorCard({ label, value, unit, min, max, color, icon, history }) {
  const pct = Math.round(Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100)));
  return (
    <div style={{
      background: "#fff", borderRadius: 13, padding: "14px 16px",
      border: `1px solid ${COLORS.border}`, display: "flex",
      flexDirection: "column", gap: 5, position: "relative", overflow: "hidden",
    }}>
      <div style={{
        position: "absolute", top: 0, left: 0,
        width: `${pct}%`, height: 3, background: color,
        borderRadius: "3px 0 0 0", transition: "width 0.7s ease",
      }} />
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontSize: 10.5, color: "#9a8f84", letterSpacing: "0.07em",
          textTransform: "uppercase", fontWeight: 500 }}>{label}</span>
        <span style={{ fontSize: 15 }}>{icon}</span>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 3 }}>
        <span style={{ fontSize: 24, fontWeight: 700, color: COLORS.earth,
          fontFamily: "'Lora', serif", lineHeight: 1 }}>{value ?? "—"}</span>
        <span style={{ fontSize: 11, color: "#9a8f84" }}>{unit}</span>
      </div>
      <Spark history={history} color={color} />
      <div style={{ display: "flex", justifyContent: "space-between",
        fontSize: 9, color: "#ccc", marginTop: 1 }}>
        <span>{min}{unit}</span><span>{max}{unit}</span>
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <div style={{
      width: 15, height: 15, borderRadius: "50%",
      border: `2px solid ${COLORS.sage}`,
      borderTopColor: "transparent",
      animation: "tg-spin 0.75s linear infinite",
      flexShrink: 0,
    }} />
  );
}

function PredictionCard({ prediction, loading, error }) {
  const cardStyle = {
    background: "#fff", borderRadius: 13, padding: "16px 18px",
    border: `1px solid ${COLORS.border}`,
  };

  if (loading) {
    return (
      <div style={cardStyle}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Spinner />
          <span style={{ fontSize: 13, color: COLORS.sage }}>Fetching prediction…</span>
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div style={cardStyle}>
        <div style={{ fontSize: 12, color: COLORS.danger }}>⚠ {error}</div>
      </div>
    );
  }
  if (!prediction) return null;

  const qColor = soilQualityColor(prediction.soil_quality);

  return (
    <div style={cardStyle}>
      <div style={{ fontSize: 10.5, color: "#9a8f84", letterSpacing: "0.07em",
        textTransform: "uppercase", fontWeight: 500, marginBottom: 12 }}>
        ML Prediction
      </div>

      <div style={{ display: "flex", alignItems: "center",
        justifyContent: "space-between", marginBottom: 14 }}>
        <div>
          <div style={{ fontSize: 10, color: "#b0a89e", marginBottom: 3 }}>Soil quality</div>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 6,
            background: qColor + "18", border: `1px solid ${qColor}44`,
            borderRadius: 20, padding: "5px 14px",
            fontSize: 13, fontWeight: 700, color: qColor,
          }}>
            {prediction.soil_quality}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 10, color: "#b0a89e", marginBottom: 3 }}>Confidence</div>
          <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.earth }}>
            {prediction.confidence}
          </div>
        </div>
      </div>

      <div style={{
        background: COLORS.mist, borderRadius: 10, padding: "12px 14px", marginBottom: 12,
      }}>
        <div style={{ fontSize: 10, color: "#9a8f84", marginBottom: 4, fontWeight: 500,
          textTransform: "uppercase", letterSpacing: "0.06em" }}>Recommended crop</div>
        <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.earth,
          fontFamily: "'Lora', serif" }}>
          {prediction.recommended_crop}
        </div>
      </div>

      {prediction.description && (
        <div style={{ fontSize: 12.5, color: "#6a5e54", lineHeight: 1.65, marginBottom: 12 }}>
          {prediction.description}
        </div>
      )}

      {prediction.recommendation && (
        <div style={{
          borderLeft: `3px solid ${COLORS.sage}`,
          paddingLeft: 10, fontSize: 12, color: "#5a4e44", lineHeight: 1.6,
        }}>
          <span style={{ fontWeight: 600, color: COLORS.moss }}>Action: </span>
          {prediction.recommendation}
        </div>
      )}
    </div>
  );
}

function Dot({ color }) {
  return (
    <span style={{
      width: 7, height: 7, borderRadius: "50%",
      background: color, display: "inline-block", flexShrink: 0,
    }} />
  );
}

export default function App() {
  const [data,        setData]        = useState(null);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [history,     setHistory]     = useState({ humidity: [], ph: [], light: [] });

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/predict/live`);
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      const json = await res.json();
      setData(json);
      setLastUpdated(new Date());
      setHistory(prev => {
        const s = json.sensor_data;
        const append = (arr, val) => [...arr.slice(-19), val];
        return {
          humidity: append(prev.humidity, s.humidity),
          ph:       append(prev.ph,       s.ph),
          light:    append(prev.light,    s.light),
        };
      });
    } catch (e) {
      setError(e.message || "Could not reach backend");
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
    const t = setInterval(fetchData, 10_000);
    return () => clearInterval(t);
  }, [fetchData]);

  const s = data?.sensor_data ?? {};
  const p = data?.prediction  ?? null;

  const sensors = [
    { key: "humidity", label: "Humidity", unit: "%",    min: 0,   max: 100,  color: COLORS.sky,  icon: "💧" },
    { key: "ph",       label: "pH Level", unit: "",     min: 4.5, max: 8.5,  color: COLORS.sage, icon: "⚗" },
    { key: "light",    label: "Light",    unit: " lux", min: 100, max: 1000, color: COLORS.amber, icon: "☀" },
  ];

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Lora:wght@600;700&family=DM+Sans:wght@400;500;600;700&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'DM Sans', sans-serif; background: #ece8e0; color: ${COLORS.earth}; min-height: 100vh; }
        @keyframes tg-spin { to { transform: rotate(360deg); } }
        @keyframes tg-fadein { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; } }
        .tg-fadein { animation: tg-fadein 0.4s ease both; }
        .tg-sensor-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
        @media (max-width: 700px) { .tg-sensor-grid { grid-template-columns: 1fr 1fr; } }
        @media (max-width: 440px) { .tg-sensor-grid { grid-template-columns: 1fr; } }
      `}</style>

      <div style={{ display: "flex", minHeight: "100vh", padding: "20px", gap: 16, alignItems: "flex-start" }}>

        {/* Sidebar */}
        <aside style={{
          width: 210, flexShrink: 0,
          background: COLORS.earth, borderRadius: 16, padding: "22px 16px",
          display: "flex", flexDirection: "column", gap: 6,
          color: "#fff", position: "sticky", top: 20,
        }}>
          <div style={{ marginBottom: 18 }}>
            <div style={{ fontSize: 10, color: "#9a8e84", letterSpacing: "0.1em",
              textTransform: "uppercase", marginBottom: 3 }}>TerraGuard</div>
            <div style={{ fontSize: 19, fontWeight: 700,
              fontFamily: "'Lora', serif", lineHeight: 1.25 }}>
              Soil<br />Intelligence
            </div>
          </div>

          <div style={{ fontSize: 10, color: "#7a6e64", letterSpacing: "0.08em",
            textTransform: "uppercase", marginBottom: 4 }}>Endpoints</div>

          {[
            { path: "GET /sensor/live",  desc: "humidity · ph · light" },
            { path: "GET /predict/live", desc: "soil quality · crop rec." },
          ].map(({ path, desc }) => (
            <div key={path} style={{
              background: "#ffffff14", borderRadius: 10, padding: "10px 12px",
              fontSize: 11.5, color: "#e0d8d0", marginBottom: 2,
            }}>
              <div style={{ fontWeight: 600, fontFamily: "monospace" }}>{path}</div>
              <div style={{ fontSize: 10, color: "#9a8e84", marginTop: 2 }}>{desc}</div>
            </div>
          ))}

          <div style={{ marginTop: "auto", paddingTop: 20, borderTop: "1px solid #5a4e44" }}>
            <div style={{ fontSize: 10, color: "#7a6e64", marginBottom: 8,
              textTransform: "uppercase", letterSpacing: "0.08em" }}>System</div>
            {[
              { label: "Backend",   color: error ? "#e07060" : "#6fcf7a" },
              { label: "RabbitMQ",  color: "#f0c040" },
              { label: "ML Model",  color: "#6fcf7a" },
              { label: "Docker",    color: "#6fcf7a" },
            ].map(({ label, color }) => (
              <div key={label} style={{ display: "flex", alignItems: "center",
                gap: 7, fontSize: 12, marginBottom: 5 }}>
                <Dot color={color} />
                <span style={{ color: "#c4b9ae" }}>{label}</span>
              </div>
            ))}
          </div>
        </aside>

        {/* Main */}
        <main style={{ flex: 1, display: "flex", flexDirection: "column", gap: 14, minWidth: 0 }}>

          {/* Header */}
          <div style={{
            background: "#fff", borderRadius: 14, padding: "16px 22px",
            border: `1px solid ${COLORS.border}`,
            display: "flex", alignItems: "center",
            justifyContent: "space-between", flexWrap: "wrap", gap: 10,
          }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 700,
                fontFamily: "'Lora', serif", color: COLORS.earth }}>
                Field Monitor
              </div>
              <div style={{ fontSize: 11, color: "#9a8f84", marginTop: 2 }}>
                Live sensor data · Random Forest soil analysis
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
              {lastUpdated && (
                <span style={{ fontSize: 11, color: "#b0a89e" }}>
                  Updated {lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                </span>
              )}
              <button
                onClick={fetchData}
                disabled={loading}
                style={{
                  background: loading ? "#e8e3dc" : COLORS.mist,
                  border: `1px solid ${COLORS.border}`,
                  borderRadius: 8, padding: "6px 14px",
                  fontSize: 12, cursor: loading ? "not-allowed" : "pointer",
                  color: COLORS.earth, fontWeight: 500,
                  display: "flex", alignItems: "center", gap: 6,
                  transition: "background 0.15s",
                }}
              >
                {loading ? <><Spinner /> Fetching…</> : "↻ Refresh"}
              </button>
            </div>
          </div>

          {/* Error banner */}
          {error && !loading && (
            <div style={{
              background: "#fff5f4", border: `1px solid #e0b0a8`,
              borderRadius: 10, padding: "10px 16px",
              fontSize: 12.5, color: COLORS.danger,
            }}>
              ⚠ {error} — make sure the backend is running on port 8000.
            </div>
          )}

          {/* Gauge row */}
          <div style={{
            background: "#fff", borderRadius: 14, padding: "16px 20px",
            border: `1px solid ${COLORS.border}`,
          }}>
            <div style={{ fontSize: 10, color: "#9a8f84", letterSpacing: "0.07em",
              textTransform: "uppercase", fontWeight: 500, marginBottom: 12 }}>
              Live sensor gauges
            </div>
            <div style={{ display: "flex", justifyContent: "space-around",
              flexWrap: "wrap", gap: 8 }}>
              {sensors.map(s2 => (
                <RadialGauge
                  key={s2.key}
                  value={s[s2.key] ?? 0}
                  min={s2.min} max={s2.max}
                  label={s2.label} unit={s2.unit}
                  color={s2.color} size={110}
                />
              ))}
            </div>
          </div>

          {/* Cards row */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 14 }}>
            <div>
              <div className="tg-sensor-grid tg-fadein">
                {sensors.map(s2 => (
                  <SensorCard
                    key={s2.key}
                    label={s2.label}
                    value={s[s2.key] ?? null}
                    unit={s2.unit}
                    min={s2.min} max={s2.max}
                    color={s2.color}
                    icon={s2.icon}
                    history={history[s2.key]}
                  />
                ))}
              </div>

              {s.field_id && (
                <div style={{
                  background: "#fff", borderRadius: 13, padding: "12px 16px",
                  border: `1px solid ${COLORS.border}`,
                  display: "flex", alignItems: "center", gap: 10, marginTop: 12,
                }}>
                  <span style={{ fontSize: 16 }}>🗺</span>
                  <div>
                    <div style={{ fontSize: 10, color: "#9a8f84", textTransform: "uppercase",
                      letterSpacing: "0.07em", fontWeight: 500 }}>Field ID</div>
                    <div style={{ fontSize: 11.5, fontFamily: "monospace",
                      color: COLORS.earth, marginTop: 2 }}>{s.field_id}</div>
                  </div>
                </div>
              )}
            </div>

            <PredictionCard
              prediction={p}
              loading={loading && !data}
              error={!loading ? error : null}
            />
          </div>

          <div style={{ fontSize: 10.5, color: "#b0a89e", textAlign: "center", paddingBottom: 6 }}>
            TerraGuard AI · POC · FastAPI + RabbitMQ + Random Forest + Docker
          </div>
        </main>
      </div>
    </>
  );
}
