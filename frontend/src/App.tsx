import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/Layout/AppLayout';
import Dashboard from './pages/Dashboard';
import Applications from './pages/Applications';
import Recommendations from './pages/Recommendations';
import TestConnection from './pages/TestConnection';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<AppLayout />}>
                    <Route index element={<Navigate to="/dashboard" replace />} />
                    <Route path="dashboard" element={<Dashboard />} />
                    <Route path="applications" element={<Applications />} />
                    <Route path="recommendations" element={<Recommendations />} />
                    <Route path="test" element={<TestConnection />} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;
