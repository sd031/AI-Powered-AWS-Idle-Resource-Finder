import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Cloud, Server, Database, HardDrive, Activity, 
  DollarSign, AlertTriangle, Download, RefreshCw,
  Settings, TrendingDown, BarChart3
} from 'lucide-react';
import './App.css';
import CredentialsForm from './components/CredentialsForm';
import ResourceTable from './components/ResourceTable';
import Dashboard from './components/Dashboard';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [activeTab, setActiveTab] = useState('credentials');
  const [profiles, setProfiles] = useState([]);
  const [regions, setRegions] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState('');
  const [selectedRegions, setSelectedRegions] = useState([]);
  const [credentials, setCredentials] = useState({
    accessKeyId: '',
    secretAccessKey: '',
    sessionToken: ''
  });
  const [useProfile, setUseProfile] = useState(true);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [enableAIFilter, setEnableAIFilter] = useState(false);
  const [aiProvider, setAiProvider] = useState('bedrock'); // 'bedrock' or 'ollama'
  const [aiStatus, setAiStatus] = useState({ available: false, status: 'checking' });
  const [analysisProgress, setAnalysisProgress] = useState({ current: 0, total: 0, region: '' });

  useEffect(() => {
    fetchProfiles();
    fetchRegions();
    checkAIStatus();
  }, []);

  const checkAIStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/ai/status`);
      setAiStatus(response.data);
    } catch (err) {
      console.error('Error checking AI status:', err);
      setAiStatus({ available: false, status: 'error' });
    }
  };

  const fetchProfiles = async () => {
    try {
      const response = await axios.get(`${API_URL}/profiles`);
      setProfiles(response.data.profiles || []);
    } catch (err) {
      console.error('Error fetching profiles:', err);
    }
  };

  const fetchRegions = async () => {
    try {
      const response = await axios.get(`${API_URL}/regions`);
      setRegions(response.data.regions || []);
    } catch (err) {
      console.error('Error fetching regions:', err);
    }
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setAnalysisProgress({ current: 0, total: 0, region: 'Starting...' });
    
    try {
      const payload = {
        regions: selectedRegions.length > 0 ? selectedRegions : null,
        enable_ai_filter: enableAIFilter,
        ai_provider: aiProvider
      };

      if (useProfile && selectedProfile) {
        payload.profile_name = selectedProfile;
      } else if (!useProfile && credentials.accessKeyId && credentials.secretAccessKey) {
        payload.credentials = {
          access_key_id: credentials.accessKeyId,
          secret_access_key: credentials.secretAccessKey,
          session_token: credentials.sessionToken || null
        };
      } else {
        setError('Please select a profile or enter AWS credentials');
        setLoading(false);
        return;
      }

      const regionsToAnalyze = payload.regions || regions;
      setAnalysisProgress({ current: 0, total: regionsToAnalyze.length, region: 'Initializing...' });
      
      const response = await axios.post(`${API_URL}/analyze`, payload);
      setAnalysisResults(response.data);
      setActiveTab('dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed');
    } finally {
      setLoading(false);
      setAnalysisProgress({ current: 0, total: 0, region: '' });
    }
  };

  const handleExportCSV = async () => {
    if (!analysisResults) return;

    try {
      const response = await axios.post(
        `${API_URL}/export/csv`,
        { resources: analysisResults.resources },
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `aws_resources_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('Failed to export CSV: ' + (err.message || 'Unknown error'));
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <Cloud size={32} />
            <h1>AWS Idle Resource Finder</h1>
          </div>
          <p className="tagline">Optimize your AWS costs by identifying underutilized resources</p>
        </div>
      </header>

      <div className="container">
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'credentials' ? 'active' : ''}`}
            onClick={() => setActiveTab('credentials')}
          >
            <Settings size={18} />
            Configuration
          </button>
          <button 
            className={`tab ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
            disabled={!analysisResults}
          >
            <BarChart3 size={18} />
            Dashboard
          </button>
          <button 
            className={`tab ${activeTab === 'resources' ? 'active' : ''}`}
            onClick={() => setActiveTab('resources')}
            disabled={!analysisResults}
          >
            <Server size={18} />
            Resources
          </button>
        </div>

        <div className="content">
          {activeTab === 'credentials' && (
            <CredentialsForm
              useProfile={useProfile}
              setUseProfile={setUseProfile}
              profiles={profiles}
              selectedProfile={selectedProfile}
              setSelectedProfile={setSelectedProfile}
              credentials={credentials}
              setCredentials={setCredentials}
              regions={regions}
              selectedRegions={selectedRegions}
              setSelectedRegions={setSelectedRegions}
              enableAIFilter={enableAIFilter}
              setEnableAIFilter={setEnableAIFilter}
              aiProvider={aiProvider}
              setAiProvider={setAiProvider}
              aiStatus={aiStatus}
              onAnalyze={handleAnalyze}
              loading={loading}
              error={error}
              analysisProgress={analysisProgress}
            />
          )}

          {activeTab === 'dashboard' && analysisResults && (
            <Dashboard 
              results={analysisResults}
              onExportCSV={handleExportCSV}
              onRefresh={handleAnalyze}
              loading={loading}
            />
          )}

          {activeTab === 'resources' && analysisResults && (
            <ResourceTable 
              resources={analysisResults.resources}
              onExportCSV={handleExportCSV}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
