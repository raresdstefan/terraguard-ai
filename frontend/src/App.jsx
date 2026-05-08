import { useEffect, useState } from "react";
import axios from "axios";

function App() {

  const [data, setData] = useState(null);

  useEffect(() => {

    fetchPrediction();

    const interval = setInterval(fetchPrediction, 5000);

    return () => clearInterval(interval);

  }, []);

  const fetchPrediction = async () => {

    try {

      const response = await axios.get(
        "http://localhost:8000/predict/live"
      );

      setData(response.data);

    } catch (error) {

      console.error(error);

    }

  };

  const getStatusColor = (quality) => {

    if (quality === "Healthy") return "#16a34a";
    if (quality === "Moderate") return "#f59e0b";

    return "#dc2626";
  };

  return (

    <div
      style={{
        background: "#f1f5f9",
        minHeight: "100vh",
        padding: "40px",
        fontFamily: "Arial"
      }}
    >

      <div
        style={{
          maxWidth: "900px",
          margin: "0 auto"
        }}
      >

        <h1
          style={{
            fontSize: "42px",
            marginBottom: "10px"
          }}
        >
          🌱 TerraGuard AI
        </h1>

        <p
          style={{
            color: "#475569",
            marginBottom: "30px"
          }}
        >
          Real-time intelligent soil monitoring system
        </p>

        {data && (

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "20px"
            }}
          >

            {/* SENSOR CARD */}

            <div
              style={{
                background: "white",
                padding: "30px",
                borderRadius: "16px",
                boxShadow: "0 4px 15px rgba(0,0,0,0.08)"
              }}
            >

              <h2>📡 Live Sensor Data</h2>

              <div style={{ marginTop: "20px" }}>

                <p>
                  <strong>Humidity:</strong>
                  {" "}
                  {data.sensor_data.humidity}%
                </p>

                <p>
                  <strong>pH:</strong>
                  {" "}
                  {data.sensor_data.ph}
                </p>

                <p>
                  <strong>Light:</strong>
                  {" "}
                  {data.sensor_data.light} lux
                </p>

              </div>

            </div>

            {/* AI CARD */}

            <div
              style={{
                background: "white",
                padding: "30px",
                borderRadius: "16px",
                boxShadow: "0 4px 15px rgba(0,0,0,0.08)"
              }}
            >

              <h2>🤖 AI Analysis</h2>

              <h1
                style={{
                  color: getStatusColor(
                    data.prediction.soil_quality
                  ),
                  marginTop: "20px"
                }}
              >
                {data.prediction.soil_quality}
              </h1>

              <p>
                <strong>Confidence:</strong>
                {" "}
                {data.prediction.confidence}
              </p>

              <hr style={{ margin: "20px 0" }} />

              <h3>🌾 Recommended Crop</h3>

              <p
                style={{
                  fontSize: "22px",
                  fontWeight: "bold"
                }}
              >
                {data.prediction.recommended_crop}
              </p>

              <p
                style={{
                  color: "#475569",
                  lineHeight: "1.6"
                }}
              >
                {data.prediction.description}
              </p>

              <div
                style={{
                  marginTop: "20px",
                  background: "#ecfeff",
                  padding: "15px",
                  borderRadius: "12px"
                }}
              >

                <strong>AI Recommendation</strong>

                <p>
                  {data.prediction.recommendation}
                </p>

              </div>

            </div>

          </div>

        )}

      </div>

    </div>

  );
}

export default App;