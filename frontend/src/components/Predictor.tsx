import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Autocomplete from './Autocomplete';
import './Predictor.css';

const Predictor: React.FC = () => {
    const [teams, setTeams] = useState<string[]>([]);
    const [homeTeam, setHomeTeam] = useState<string>('');
    const [awayTeam, setAwayTeam] = useState<string>('');
    const [homeLogo, setHomeLogo] = useState<string>('');
    const [awayLogo, setAwayLogo] = useState<string>('');
    const [prediction, setPrediction] = useState<any>(null);
    const [matchDetails, setMatchDetails] = useState<any>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [detailsLoading, setDetailsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string>('');

    useEffect(() => {
        axios.get('/api/teams')
            .then(response => {
                setTeams(response.data.teams);
            })
            .catch(err => {
                console.error("Error fetching teams:", err);
                setError('Could not load team list. Is the backend running?');
            });
    }, []);

    const fetchLogo = async (teamName: string, setLogo: (url: string) => void) => {
        if (!teamName) return;
        try {
            const response = await axios.get(`/api/team-logo/${teamName}`);
            if (response.data.logoUrl) {
                setLogo(response.data.logoUrl);
            }
        } catch (err) {
            console.error(`Error fetching logo for ${teamName}:`, err);
            setLogo(''); // Reset logo on error
        }
    };

    useEffect(() => {
        fetchLogo(homeTeam, setHomeLogo);
    }, [homeTeam]);

    useEffect(() => {
        fetchLogo(awayTeam, setAwayLogo);
    }, [awayTeam]);

    const handlePredict = () => {
        if (!homeTeam || !awayTeam) {
            setError('Please select both teams.');
            return;
        }
        if (homeTeam === awayTeam) {
            setError('Please select two different teams.');
            return;
        }
        
        setLoading(true);
        setError('');
        setPrediction(null);
        setMatchDetails(null);

        axios.post('/api/predict', { home_team: homeTeam, away_team: awayTeam })
            .then(response => {
                setPrediction(response.data);
                setDetailsLoading(true);
                axios.post('/api/match-details', { home_team: homeTeam, away_team: awayTeam })
                    .then(detailsResponse => {
                        setMatchDetails(detailsResponse.data);
                    })
                    .catch(err => {
                        console.error("Error fetching match details:", err);
                    })
                    .finally(() => {
                        setDetailsLoading(false);
                    });
            })
            .catch(err => {
                console.error("Error making prediction:", err);
                setError('Prediction failed. Please try again.');
            })
            .finally(() => {
                setLoading(false);
            });
    };

    const getWinnerLogo = () => {
        if (!prediction) return null;
        switch (prediction.prediction) {
            case "Victoire à domicile":
                return homeLogo;
            case "Victoire à l'extérieur":
                return awayLogo;
            default:
                return null;
        }
    };

    return (
        <div className="predictor-container">
            <h1>Match Predictor</h1>
            <p>Select two teams to predict the outcome and score.</p>
            {error && <p className="error">{error}</p>}
            <div className="selection-area">
                <div className="team-selector">
                    {homeLogo && <img src={homeLogo} alt={`${homeTeam} logo`} className="team-logo" />}
                    <label>Home Team</label>
                    <Autocomplete 
                        suggestions={teams}
                        value={homeTeam}
                        onChange={setHomeTeam}
                        onSelect={setHomeTeam}
                    />
                </div>
                <div className="vs">VS</div>
                <div className="team-selector">
                    {awayLogo && <img src={awayLogo} alt={`${awayTeam} logo`} className="team-logo" />}
                    <label>Away Team</label>
                    <Autocomplete 
                        suggestions={teams}
                        value={awayTeam}
                        onChange={setAwayTeam}
                        onSelect={setAwayTeam}
                    />
                </div>
            </div>
            <button onClick={handlePredict} disabled={loading || teams.length === 0}>
                {loading ? 'Predicting...' : 'Predict'}
            </button>

            {prediction && (
                <div className="prediction-result">
                    <h2>Prediction</h2>
                    <div className="result-card">
                        <div className="winner-info">
                            {getWinnerLogo() && <img src={getWinnerLogo()!} alt="winner logo" className="winner-logo"/>}
                            <p className="prediction-text">{prediction.prediction}</p>
                        </div>
                        {prediction.score && <p className="score-text">Predicted Score: {prediction.score}</p>}
                        {prediction.probabilities && (
                            <div className="probabilities">
                                <div className="prob-item">{homeTeam}: <span>{`${(prediction.probabilities.home_win * 100).toFixed(0)}%`}</span></div>
                                <div className="prob-item">Draw: <span>{`${(prediction.probabilities.draw * 100).toFixed(0)}%`}</span></div>
                                <div className="prob-item">{awayTeam}: <span>{`${(prediction.probabilities.away_win * 100).toFixed(0)}%`}</span></div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {detailsLoading && <div className="text-center"><div className="spinner-border" role="status"><span className="visually-hidden">Loading...</span></div></div>}

            {matchDetails && (
                <div className="match-details">
                    <h2>Match Details</h2>
                    <div className="details-card">
                        <h3>Head-to-Head</h3>
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Home Team</th>
                                    <th>Score</th>
                                    <th>Away Team</th>
                                </tr>
                            </thead>
                            <tbody>
                                {matchDetails.head_to_head.map((match: any) => (
                                    <tr key={match.date}>
                                        <td>{new Date(match.date).toLocaleDateString()}</td>
                                        <td>{match.home_team}</td>
                                        <td>{match.home_goals} - {match.away_goals}</td>
                                        <td>{match.away_team}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>

                        <h3>{homeTeam} - Recent Form</h3>
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Home Team</th>
                                    <th>Score</th>
                                    <th>Away Team</th>
                                </tr>
                            </thead>
                            <tbody>
                                {matchDetails.home_team_form.map((match: any) => (
                                    <tr key={match.date}>
                                        <td>{new Date(match.date).toLocaleDateString()}</td>
                                        <td>{match.home_team}</td>
                                        <td>{match.home_goals} - {match.away_goals}</td>
                                        <td>{match.away_team}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>

                        <h3>{awayTeam} - Recent Form</h3>
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Home Team</th>
                                    <th>Score</th>
                                    <th>Away Team</th>
                                </tr>
                            </thead>
                            <tbody>
                                {matchDetails.away_team_form.map((match: any) => (
                                    <tr key={match.date}>
                                        <td>{new Date(match.date).toLocaleDateString()}</td>
                                        <td>{match.home_team}</td>
                                        <td>{match.home_goals} - {match.away_goals}</td>
                                        <td>{match.away_team}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Predictor;
