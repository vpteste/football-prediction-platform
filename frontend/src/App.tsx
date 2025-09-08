import { useState, useEffect } from 'react';
import './App.css';

interface Prediction {
  id: number;
  match: string;
  prediction: string;
  confidence: string;
  competition?: { name: string; };
  utcDate?: string;
}

// Type pour stocker les votes : clé = id du match, valeur = 'H' (domicile) ou 'A' (extérieur)
type Votes = Record<number, 'H' | 'A'>;

function App() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [votes, setVotes] = useState<Votes>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Charger les votes depuis le Local Storage au démarrage
  useEffect(() => {
    try {
      const savedVotes = localStorage.getItem('football_votes');
      if (savedVotes) {
        setVotes(JSON.parse(savedVotes));
      }
    } catch (e) {
      console.error("Erreur lors du chargement des votes:", e);
    }
  }, []);

  // Sauvegarder les votes dans le Local Storage à chaque changement
  useEffect(() => {
    try {
      localStorage.setItem('football_votes', JSON.stringify(votes));
    } catch (e) {
      console.error("Erreur lors de la sauvegarde des votes:", e);
    }
  }, [votes]);

  useEffect(() => {
    const fetchPredictions = async () => {
      // ... (le reste de la logique de fetch reste la même)
      try {
        const response = await fetch('/api/predictions');
        if (!response.ok) throw new Error(`Erreur HTTP: ${response.status}`);
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        setPredictions(data.predictions || []);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchPredictions();
  }, []);

  const handleVote = (matchId: number, outcome: 'H' | 'A') => {
    setVotes(prevVotes => ({
      ...prevVotes,
      [matchId]: outcome
    }));
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Date inconnue';
    return new Date(dateString).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' });
  };

  return (
    <div className="d-flex flex-column min-vh-100 bg-light">
      <nav className="navbar navbar-dark bg-dark shadow-sm">
        <div className="container-fluid">
          <span className="navbar-brand mb-0 h1">⚽ Top 10 Prédictions IA</span>
        </div>
      </nav>

      <main className="container my-4">
        {/* ... (Gestion du chargement et des erreurs) ... */}

        {!loading && !error && (
          <div className="row g-4">
            {predictions.length > 0 ? (
              predictions.map((p) => {
                const [homeTeam, awayTeam] = p.match.split(' vs ');
                const userVote = votes[p.id];

                return (
                  <div key={p.id} className="col-lg-6">
                    <div className="card h-100 shadow-sm prediction-card">
                      <div className="card-header text-white bg-primary">
                        <h5 className="card-title mb-0 text-truncate">{p.match}</h5>
                        <small>{p.competition?.name || 'N/A'}</small>
                      </div>
                      <div className="card-body pb-0">
                        <p className="card-text"><strong>Prédiction IA :</strong> {p.prediction}</p>
                        <p className="card-text"><small className="text-muted">{formatDate(p.utcDate)}</small></p>
                        <div className="d-flex align-items-center mb-3">
                          <strong className="me-2">Confiance IA:</strong>
                          <div className="progress flex-grow-1" style={{ height: '20px' }}>
                            <div className="progress-bar bg-success" role="progressbar" style={{ width: p.confidence }} aria-valuenow={parseInt(p.confidence)} aria-valuemin={0} aria-valuemax={100}>{p.confidence}</div>
                          </div>
                        </div>
                      </div>
                      <div className="card-footer text-center">
                        <p className="mb-2 small text-muted">Votre vote :</p>
                        <div className="btn-group w-100">
                          <button 
                            className={`btn ${userVote === 'H' ? 'btn-primary' : 'btn-outline-primary'}`}
                            onClick={() => handleVote(p.id, 'H')}
                          >
                            {homeTeam}
                          </button>
                          <button 
                            className={`btn ${userVote === 'A' ? 'btn-primary' : 'btn-outline-primary'}`}
                            onClick={() => handleVote(p.id, 'A')}
                          >
                            {awayTeam}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-center text-muted mt-5">
                <h4>Aucune prédiction disponible</h4>
                <p>Le modèle n'a trouvé aucun match à venir avec une confiance suffisante.</p>
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="text-center text-muted py-3 mt-auto bg-white border-top">
        <small>&copy; {new Date().getFullYear()} Football Prediction Platform</small>
      </footer>
    </div>
  );
}

export default App;
