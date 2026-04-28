import React, { useState, useEffect } from 'react';
import { Play, AlertCircle, RefreshCw, Brain, Sparkles } from 'lucide-react';

function CredentialsForm({ 
  useProfile, 
  setUseProfile, 
  profiles, 
  selectedProfile, 
  setSelectedProfile,
  credentials,
  setCredentials,
  regions,
  selectedRegions,
  setSelectedRegions,
  enableAIFilter,
  setEnableAIFilter,
  aiProvider,
  setAiProvider,
  aiStatus,
  onAnalyze,
  loading,
  error,
  analysisProgress
}) {
  const handleRegionToggle = (region) => {
    if (selectedRegions.includes(region)) {
      setSelectedRegions(selectedRegions.filter(r => r !== region));
    } else {
      setSelectedRegions([...selectedRegions, region]);
    }
  };

  const selectAllRegions = () => {
    setSelectedRegions(regions);
  };

  const clearAllRegions = () => {
    setSelectedRegions([]);
  };

  return (
    <div className="form-section">
      <h2>AWS Configuration</h2>
      
      <div className="toggle-group">
        <button
          className={`toggle-btn ${useProfile ? 'active' : ''}`}
          onClick={() => setUseProfile(true)}
        >
          Use AWS Profile
        </button>
        <button
          className={`toggle-btn ${!useProfile ? 'active' : ''}`}
          onClick={() => setUseProfile(false)}
        >
          Enter Credentials
        </button>
      </div>

      {useProfile ? (
        <div className="form-group">
          <label>AWS Profile</label>
          <select
            value={selectedProfile}
            onChange={(e) => setSelectedProfile(e.target.value)}
          >
            <option value="">Select a profile...</option>
            {profiles.map(profile => (
              <option key={profile} value={profile}>{profile}</option>
            ))}
          </select>
          {profiles.length === 0 && (
            <p style={{ color: '#666', fontSize: '0.9rem', marginTop: '0.5rem' }}>
              No AWS profiles found in ~/.aws/credentials
            </p>
          )}
        </div>
      ) : (
        <>
          <div className="form-group">
            <label>AWS Access Key ID</label>
            <input
              type="text"
              value={credentials.accessKeyId}
              onChange={(e) => setCredentials({ ...credentials, accessKeyId: e.target.value })}
              placeholder="AKIAIOSFODNN7EXAMPLE"
            />
          </div>
          <div className="form-group">
            <label>AWS Secret Access Key</label>
            <input
              type="password"
              value={credentials.secretAccessKey}
              onChange={(e) => setCredentials({ ...credentials, secretAccessKey: e.target.value })}
              placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
            />
          </div>
          <div className="form-group">
            <label>Session Token (Optional)</label>
            <input
              type="password"
              value={credentials.sessionToken}
              onChange={(e) => setCredentials({ ...credentials, sessionToken: e.target.value })}
              placeholder="For temporary credentials"
            />
          </div>
        </>
      )}

      <div className="form-group ai-filter-section">
        <div style={{ 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          padding: '1.5rem',
          borderRadius: '12px',
          color: 'white',
          marginBottom: '1.5rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <Brain size={24} />
            <h3 style={{ margin: 0, fontSize: '1.2rem' }}>AI-Powered Filtering</h3>
            <Sparkles size={20} />
          </div>
          <p style={{ margin: '0 0 1rem 0', opacity: 0.9, fontSize: '0.95rem' }}>
            Use local LLM (Llama 3.2) to intelligently filter resources and identify what's truly idle.
            AI analyzes context, usage patterns, and resource characteristics beyond simple CPU metrics.
          </p>
          
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column',
            gap: '1rem',
            background: 'rgba(255, 255, 255, 0.15)',
            padding: '1rem',
            borderRadius: '8px'
          }}>
            <label style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '0.5rem',
              cursor: 'pointer'
            }}>
              <input
                type="checkbox"
                checked={enableAIFilter}
                onChange={(e) => setEnableAIFilter(e.target.checked)}
                style={{ width: '18px', height: '18px', cursor: 'pointer' }}
              />
              <span style={{ fontWeight: '600' }}>Enable AI Filtering</span>
            </label>
            
            {enableAIFilter && (
              <div style={{ paddingLeft: '1.5rem' }}>
                <label style={{ fontSize: '0.9rem', marginBottom: '0.5rem', display: 'block', opacity: 0.9 }}>
                  AI Provider:
                </label>
                <select
                  value={aiProvider || 'bedrock'}
                  onChange={(e) => setAiProvider(e.target.value)}
                  style={{
                    padding: '0.5rem',
                    borderRadius: '6px',
                    border: '1px solid rgba(255, 255, 255, 0.3)',
                    background: 'rgba(255, 255, 255, 0.1)',
                    color: 'white',
                    fontSize: '0.9rem',
                    cursor: 'pointer',
                    width: '100%'
                  }}
                >
                  <option value="bedrock" style={{ background: '#667eea', color: 'white' }}>
                    🚀 Amazon Bedrock (Claude 3.5) - Recommended
                  </option>
                  <option value="ollama" style={{ background: '#667eea', color: 'white' }}>
                    🏠 Local Ollama (Llama 3.2)
                  </option>
                </select>
              </div>
            )}
            
            <div style={{ 
              padding: '0.5rem 1rem',
              background: aiStatus?.available ? 'rgba(76, 175, 80, 0.3)' : 'rgba(255, 152, 0, 0.3)',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: '500'
            }}>
              {aiStatus?.available ? '✓ AI Ready' : '⚠ AI Loading...'}
            </div>
          </div>
          
          {enableAIFilter && aiProvider === 'ollama' && (
            <div style={{ 
              marginTop: '1rem',
              padding: '0.75rem',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '6px',
              fontSize: '0.85rem'
            }}>
              <strong>Note:</strong> First-time use may take 2-3 minutes to download the AI model (~2GB).
              Subsequent analyses will be faster.
            </div>
          )}
          {enableAIFilter && aiProvider === 'bedrock' && (
            <div style={{ 
              marginTop: '1rem',
              padding: '0.75rem',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '6px',
              fontSize: '0.85rem'
            }}>
              <strong>Note:</strong> Uses AWS Bedrock with Claude 3.5 Sonnet. Requires Bedrock access in your AWS account.
              Fast and reliable AI analysis.
            </div>
          )}
        </div>
      </div>

      <div className="form-group">
        <label>
          Regions to Analyze 
          <span style={{ fontSize: '0.9rem', color: '#666', marginLeft: '0.5rem' }}>
            (Leave empty to analyze all regions)
          </span>
        </label>
        <div style={{ marginBottom: '0.5rem' }}>
          <button 
            onClick={selectAllRegions}
            style={{ 
              marginRight: '0.5rem', 
              padding: '0.5rem 1rem',
              border: '1px solid #667eea',
              background: 'white',
              color: '#667eea',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Select All
          </button>
          <button 
            onClick={clearAllRegions}
            style={{ 
              padding: '0.5rem 1rem',
              border: '1px solid #999',
              background: 'white',
              color: '#666',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Clear All
          </button>
        </div>
        <div className="region-selector">
          {regions.map(region => (
            <div key={region} className="region-checkbox">
              <input
                type="checkbox"
                id={region}
                checked={selectedRegions.includes(region)}
                onChange={() => handleRegionToggle(region)}
              />
              <label htmlFor={region}>{region}</label>
            </div>
          ))}
        </div>
      </div>

      <div className="button-group">
        <button 
          className="btn btn-primary" 
          onClick={onAnalyze}
          disabled={loading}
        >
          {loading ? (
            <>
              <RefreshCw className="spinner" size={20} />
              Analyzing...
            </>
          ) : (
            <>
              <Play size={20} />
              Start Analysis
            </>
          )}
        </button>
      </div>

      {loading && analysisProgress && analysisProgress.total > 0 && (
        <div style={{
          marginTop: '1.5rem',
          padding: '1.5rem',
          background: 'linear-gradient(135deg, #667eea15 0%, #764ba215 100%)',
          borderRadius: '12px',
          border: '1px solid #667eea30'
        }}>
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '0.5rem'
            }}>
              <span style={{ 
                fontSize: '0.95rem', 
                fontWeight: '600',
                color: '#667eea'
              }}>
                {analysisProgress.region || 'Processing...'}
              </span>
              <span style={{ 
                fontSize: '0.9rem', 
                color: '#666'
              }}>
                {analysisProgress.current}/{analysisProgress.total} regions
              </span>
            </div>
            <div style={{
              width: '100%',
              height: '8px',
              background: '#e5e7eb',
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                height: '100%',
                background: 'linear-gradient(90deg, #667eea, #764ba2)',
                width: `${(analysisProgress.current / analysisProgress.total) * 100}%`,
                transition: 'width 0.3s ease',
                borderRadius: '4px'
              }}></div>
            </div>
          </div>
          <p style={{ 
            margin: 0, 
            fontSize: '0.85rem', 
            color: '#666',
            textAlign: 'center'
          }}>
            Scanning AWS resources across selected regions...
          </p>
        </div>
      )}

      {error && (
        <div className="error-message">
          <AlertCircle size={20} />
          {error}
        </div>
      )}
    </div>
  );
}

export default CredentialsForm;
