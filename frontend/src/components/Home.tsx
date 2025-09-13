import { useState, useEffect } from 'react';
import '../App.css';

interface Prediction {
  id: number;
  match: string;
  prediction: string;
  confidence: string;
  score?: string;
  competition?: { name: string; };
  utcDate?: string;
}

const Home: React.FC = () => {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPredictions = async () => {
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

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Date inconnue';
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  };

  return (
    <main className="container my-4">
        <div className="text-center mb-4">
            <h1>Prédictions des Matchs à Venir</h1>
            <p className="lead">Voici les 10 prochains matchs avec les prédictions de notre modèle.</p>
        </div>

      {loading && <div className="text-center"><div className="spinner-border" role="status"><span className="visually-hidden">Loading...</span></div></div>}
      {error && <div className="alert alert-danger">Erreur: {error}</div>}
      {!loading && !error && (
        <div className="row g-4">
          {predictions.length > 0 ? (
            predictions.map((p) => {
              const [homeTeam, awayTeam] = p.match.split(' vs ');

              return (
                <div key={p.id} className="col-12">
                  <div className="card shadow-sm prediction-card-horizontal">
                    <div className="card-body">
                        <div className="match-info">
                            <span className="competition-name">{p.competition?.name || 'N/A'}</span>
                            <span className="match-date">{formatDate(p.utcDate)}</span>
                        </div>
                        <div className="teams-and-score">
                            <div className="team-info">
                                <span>{homeTeam}</span>
                            </div>
                            <div className="score-prediction">
                                <span className="score">{p.score || '-'}</span>
                                <span className="prediction-outcome">{p.prediction}</span>
                            </div>
                            <div className="team-info away">
                                <span>{awayTeam}</span>
                            </div>
                        </div>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-center text-muted mt-5">
              <h4>Aucune prédiction disponible</h4>
              <p>Aucun match à venir n'a été trouvé pour le moment. Veuillez réessayer plus tard.</p>
            </div>
          )}
        </div>
      )}
    </main>
  );
}

export default Home;
