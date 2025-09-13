import { useState } from 'react';
import './App.css';

function App() {
  const [species, setSpecies] = useState('');
  const [years, setYears] = useState(20);
  const [trees, setTrees] = useState(100);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await fetch('http://localhost:5000/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ species, years, trees })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Unknown error');
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="afforestation-app">
      <header>
        <h1>🌳 Afforestation Impact Model</h1>
        <p>Estimate CO₂ sequestration by planting trees</p>
      </header>
      <form className="input-form" onSubmit={handleSubmit}>
        <label>
          Tree Species:
          <input
            type="text"
            value={species}
            onChange={e => setSpecies(e.target.value)}
            placeholder="e.g. Terminalia arjuna"
            required
          />
        </label>
        <label>
          Years:
          <input
            type="number"
            min={1}
            value={years}
            onChange={e => setYears(e.target.value)}
            required
          />
        </label>
        <label>
          Number of Trees:
          <input
            type="number"
            min={1}
            value={trees}
            onChange={e => setTrees(e.target.value)}
            required
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? 'Calculating...' : 'Simulate'}
        </button>
      </form>
      {error && <div className="error">❌ {error}</div>}
      {result && (
        <div className="results">
          <h2>Results</h2>
          <p className="summary">{result.summary}</p>
          <div className="chart">
            <h3>CO₂ Sequestered Over Time</h3>
            <ul>
              {result.results.map((row, idx) => (
                <li key={idx}>
                  Year {row.age_years}: <b>{row.Total_CO2_sequestered.toFixed(2)} kg</b>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
      <footer>
        <p>Made with 🌱 for a greener future</p>
      </footer>
    </div>
  );
}

export default App;
