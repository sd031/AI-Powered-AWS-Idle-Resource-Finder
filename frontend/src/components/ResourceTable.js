import React, { useState } from 'react';
import { Download, Search } from 'lucide-react';

function ResourceTable({ resources, onExportCSV }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterRecommendation, setFilterRecommendation] = useState('all');

  const hasAIAnalysis = resources.length > 0 && resources.some(r => r.ai_analysis);

  const getRecommendationBadge = (recommendation) => {
    if (recommendation.includes('Idle') || recommendation.includes('Terminating')) {
      return 'badge-idle';
    } else if (recommendation.includes('Low')) {
      return 'badge-low';
    } else if (recommendation.includes('Moderate')) {
      return 'badge-moderate';
    } else if (recommendation.includes('Active')) {
      return 'badge-active';
    } else if (recommendation.includes('Stopped')) {
      return 'badge-stopped';
    }
    return 'badge-moderate';
  };

  const resourceTypes = [...new Set(resources.map(r => r.resource_type))];
  
  const filteredResources = resources.filter(resource => {
    const matchesSearch = 
      resource.resource_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      resource.resource_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      resource.region.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesType = filterType === 'all' || resource.resource_type === filterType;
    
    const matchesRecommendation = 
      filterRecommendation === 'all' || 
      resource.recommendation.toLowerCase().includes(filterRecommendation.toLowerCase());
    
    return matchesSearch && matchesType && matchesRecommendation;
  });

  return (
    <div>
      <div className="actions">
        <button className="btn btn-secondary" onClick={onExportCSV}>
          <Download size={18} />
          Export to CSV
        </button>
      </div>

      <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <div style={{ flex: '1', minWidth: '250px' }}>
          <div style={{ position: 'relative' }}>
            <Search 
              size={18} 
              style={{ 
                position: 'absolute', 
                left: '12px', 
                top: '50%', 
                transform: 'translateY(-50%)',
                color: '#999'
              }} 
            />
            <input
              type="text"
              placeholder="Search resources..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ 
                width: '100%',
                paddingLeft: '40px',
                padding: '0.75rem',
                border: '2px solid #e0e0e0',
                borderRadius: '8px',
                fontSize: '1rem'
              }}
            />
          </div>
        </div>

        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          style={{ 
            padding: '0.75rem',
            border: '2px solid #e0e0e0',
            borderRadius: '8px',
            fontSize: '1rem',
            minWidth: '200px'
          }}
        >
          <option value="all">All Resource Types</option>
          {resourceTypes.map(type => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>

        <select
          value={filterRecommendation}
          onChange={(e) => setFilterRecommendation(e.target.value)}
          style={{ 
            padding: '0.75rem',
            border: '2px solid #e0e0e0',
            borderRadius: '8px',
            fontSize: '1rem',
            minWidth: '200px'
          }}
        >
          <option value="all">All Recommendations</option>
          <option value="idle">Idle Resources</option>
          <option value="low">Low Utilization</option>
          <option value="moderate">Moderate Utilization</option>
          <option value="active">Active Resources</option>
          <option value="stopped">Stopped Resources</option>
        </select>
      </div>

      <div style={{ marginBottom: '1rem', color: '#666' }}>
        Showing {filteredResources.length} of {resources.length} resources
      </div>

      <div className="resource-table-container">
        <table className="resource-table">
          <thead>
            <tr>
              <th>Region</th>
              <th>Type</th>
              <th>Resource Name</th>
              <th>Resource ID</th>
              <th>Instance Type</th>
              <th>State</th>
              <th>Monthly Cost</th>
              <th>CPU Util %</th>
              <th>Recommendation</th>
              {hasAIAnalysis && (
                <>
                  <th>AI Confidence</th>
                  <th>AI Reasoning</th>
                </>
              )}
              <th>Created Date</th>
            </tr>
          </thead>
          <tbody>
            {filteredResources.length === 0 ? (
              <tr>
                <td colSpan={hasAIAnalysis ? "12" : "10"} style={{ textAlign: 'center', padding: '2rem', color: '#999' }}>
                  No resources found matching your filters
                </td>
              </tr>
            ) : (
              filteredResources.map((resource, idx) => (
                <tr key={idx}>
                  <td>{resource.region}</td>
                  <td>{resource.resource_type}</td>
                  <td>{resource.resource_name}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                    {resource.resource_id}
                  </td>
                  <td>{resource.instance_type || '-'}</td>
                  <td>{resource.state}</td>
                  <td>${resource.monthly_cost_usd.toFixed(2)}</td>
                  <td>{resource.cpu_utilization_avg.toFixed(1)}%</td>
                  <td>
                    <span className={`badge ${getRecommendationBadge(resource.recommendation)}`}>
                      {resource.recommendation}
                    </span>
                  </td>
                  {hasAIAnalysis && (
                    <>
                      <td>
                        <span style={{ 
                          padding: '0.25rem 0.5rem',
                          background: '#e8f5e9',
                          color: '#2e7d32',
                          borderRadius: '4px',
                          fontSize: '0.85rem',
                          fontWeight: '600'
                        }}>
                          {resource.ai_analysis?.ai_confidence || 0}%
                        </span>
                      </td>
                      <td style={{ fontSize: '0.85rem', maxWidth: '300px' }}>
                        {resource.ai_analysis?.ai_reasoning || '-'}
                      </td>
                    </>
                  )}
                  <td>
                    {resource.created_date ? 
                      new Date(resource.created_date).toLocaleDateString() : 
                      '-'
                    }
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ResourceTable;
