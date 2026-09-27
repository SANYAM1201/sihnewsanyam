import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Launch from './pages/Launch/Launch';
import Dashboard from './pages/Dashboard';
import Reports from './pages/Reports/Reports';
import LiveSurvey from './pages/LiveSurvey';
import AnomalyInspector from './pages/AnomalyInspector';
import Health from './pages/Health';
import Settings from './pages/Settings';
import ApiDocs from './pages/ApiDocs';
import Map from './pages/Map/Map';
import Uploads from './pages/Uploads/Uploads';
import DetectionResults from './pages/DetectionResults/DetectionResults';
import './App.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Core Scan Launch Workflow */}
        <Route path="/" element={<Launch />} />
        <Route path="/launch" element={<Navigate to="/" replace />} />

        {/* Operational Intelligence Pages */}
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/live-survey" element={<LiveSurvey />} />
        <Route path="/map" element={<Map />} />
        <Route path="/anomalies" element={<AnomalyInspector />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/uploads" element={<Uploads />} />
        <Route path="/results" element={<Navigate to="/uploads" replace />} />
        <Route path="/results/:runId" element={<DetectionResults />} />

        {/* Cluster Management & Docs */}
        <Route path="/health" element={<Health />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/api-docs" element={<ApiDocs />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
