
import React, { useState } from 'react';
import "./App.css";

function App() {
  const [mapType, setMapType] = useState('daily');
  const [loading, setLoading] = useState(false);
  const [imageUrl, setImageUrl] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();

    setLoading(true);

    const formData = new FormData(event.target);

    const mapType = formData.get("map_type");
    
    let body;
    if (mapType === "daily")
      body = {'type' : "daily_snowfall", 'sdate': formData.get("sdate"), 'edate': formData.get("edate")}
    else if (mapType === "seasonal")
      body = {'type' : 'seasonal_snowfall', 'syear': formData.get("syear")}
    else
      body = {'type' : 'average_snowfall'}
  
    const params = encodeURIComponent(JSON.stringify(body));

    const response = await fetch(`/getmap?params=${params}`, {
      method: 'GET'
    });

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    setImageUrl(url);

    setLoading(false);
  }

  return (
    <div className="App">
      <form onSubmit={handleSubmit}>
        <h3>Select the type of map you want to generate</h3>
        <select name="map_type"  value={mapType} onChange={(e) => setMapType(e.target.value)}>
          <option value="daily">Daily</option>
          <option value="seasonal">Seasonal</option>
          <option value="average">Average</option>
        </select>
        {(mapType === "daily") && 
          <>
            <h3>Select the starting date</h3>
            <input name="sdate" placeholder="yyyy-mm-dd" autoComplete="off"/>
            <h3>Select the ending date</h3>
            <input name="edate" placeholder="yyyy-mm-dd" autoComplete="off"/>
          </>
        }
        {(mapType === "seasonal") && 
          <>
            <h3>Select the starting year</h3>
            <input name="syear" placeholder="yyyy" autoComplete="off"/>
          </>
        }
        <br/>
        <br/>
        <button type="submit">Create Map</button>
      </form>
      {loading && <h1>Image is generating...</h1>}
      {!loading && <img id="snow_map" src={imageUrl} alt={"Snow Map"}/>}
    </div>
  );
}

export default App;
