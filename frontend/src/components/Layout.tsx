import React from 'react';
import { Outlet, Link } from 'react-router-dom';

const Layout: React.FC = () => {
    return (
        <div className="d-flex flex-column min-vh-100 bg-light">
            <nav className="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm">
                <div className="container-fluid">
                    <Link className="navbar-brand mb-0 h1" to="/">⚽ Football Predictor</Link>
                    <div className="collapse navbar-collapse">
                        <ul className="navbar-nav me-auto mb-2 mb-lg-0">
                            <li className="nav-item">
                                <Link className="nav-link" to="/">Top 10 Predictions</Link>
                            </li>
                            <li className="nav-item">
                                <Link className="nav-link" to="/predict">Predict Match</Link>
                            </li>
                        </ul>
                    </div>
                </div>
            </nav>

            <Outlet /> 

            <footer className="text-center text-muted py-3 mt-auto bg-white border-top">
                <small>&copy; {new Date().getFullYear()} Football Prediction Platform</small>
            </footer>
        </div>
    );
};

export default Layout;
