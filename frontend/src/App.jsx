import { useEffect, useState } from 'react';
import axios from 'axios';

function App() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchData();

    const interval = setInterval(fetchData, 5000);

    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    const response = await axios.get('http://localhost:8000/sensor/live');
    setData(response.data);
  };

  return (
    <div style={{ padding: 40, fontFamily: 'Arial' }}>
      <h1>TerraGuard AI Dashboard</h1>

      {data && (
        <div>
          <h2>Live Soil Data</h2>
          <p>Humidity: {data.humidity}%</p>
          <p>pH: {data.ph}</p>
          <p>Light: {data.light} lux</p>
        </div>
      )}
    </div>
  );
}

export default App;
