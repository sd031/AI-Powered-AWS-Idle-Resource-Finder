import React from 'react';
import { 
  Server, DollarSign, AlertTriangle, TrendingDown,
  Download, RefreshCw, Database, HardDrive, Activity, Brain, Sparkles
} from 'lucide-react';

function Dashboard({ results, onExportCSV, onRefresh, loading }) {
  const aiFilteringEnabled = results.ai_filtering?.enabled || false;
  const getResourceTypeCount = (type) => {
    return results.resources.filter(r => r.resource_type.includes(type)).length;
  };

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

  const idleResources = results.resources.filter(r => 
    r.recommendation.includes('Idle') || r.recommendation.includes('Terminating')
  );

  return (
    <div>
      <div className="actions">
        <button className="btn btn-secondary" onClick={onRefresh} disabled={loading}>
          <RefreshCw size={18} />
          Refresh Analysis
        </button>
        <button className="btn btn-secondary" onClick={onExportCSV}>
          <Download size={18} />
          Export to CSV
        </button>
      </div>

      {aiFilteringEnabled && (
        <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: '1rem 1.5rem',
          borderRadius: '12px',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <Brain size={24} />
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <strong style={{ fontSize: '1.1rem' }}>AI Filtering Active</strong>
              <Sparkles size={16} />
            </div>
            <div style={{ fontSize: '0.9rem', opacity: 0.95 }}>
              Analyzed {results.ai_filtering.total_candidates} candidates, 
              found {results.ai_filtering.truly_idle_count} truly idle resources using {results.ai_filtering.ai_model}
            </div>
          </div>
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-header">
            <Server size={24} />
            <span>Total Resources</span>
          </div>
          <div className="stat-card-value">{results.total_resources}</div>
          <div className="stat-card-label">Across {results.analyzed_regions.length} regions</div>
        </div>

        <div className="stat-card success">
          <div className="stat-card-header">
            <DollarSign size={24} />
            <span>Monthly Cost</span>
          </div>
          <div className="stat-card-value">${results.total_monthly_cost.toFixed(2)}</div>
          <div className="stat-card-label">Estimated total spend</div>
        </div>

        <div className="stat-card warning">
          <div className="stat-card-header">
            <AlertTriangle size={24} />
            <span>Idle Resources</span>
          </div>
          <div className="stat-card-value">{results.idle_resources_count}</div>
          <div className="stat-card-label">Underutilized or stopped</div>
        </div>

        <div className="stat-card warning">
          <div className="stat-card-header">
            <TrendingDown size={24} />
            <span>Potential Savings</span>
          </div>
          <div className="stat-card-value">${results.potential_savings.toFixed(2)}</div>
          <div className="stat-card-label">Per month</div>
        </div>
      </div>

      <div style={{ marginTop: '2rem' }}>
        <h3 style={{ marginBottom: '1rem', color: '#333' }}>Resource Breakdown</h3>
        <div className="stats-grid">
          <div className="stat-card" style={{ background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' }}>
            <div className="stat-card-header">
              <Server size={20} />
              <span>EC2 Instances</span>
            </div>
            <div className="stat-card-value">{getResourceTypeCount('EC2')}</div>
          </div>

          <div className="stat-card" style={{ background: 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)' }}>
            <div className="stat-card-header">
              <Database size={20} />
              <span>RDS Instances</span>
            </div>
            <div className="stat-card-value">{getResourceTypeCount('RDS')}</div>
          </div>

          <div className="stat-card" style={{ background: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)' }}>
            <div className="stat-card-header">
              <HardDrive size={20} />
              <span>EBS Volumes</span>
            </div>
            <div className="stat-card-value">{getResourceTypeCount('EBS')}</div>
          </div>

          <div className="stat-card" style={{ background: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)' }}>
            <div className="stat-card-header">
              <Activity size={20} />
              <span>Load Balancers</span>
            </div>
            <div className="stat-card-value">{getResourceTypeCount('Load Balancer')}</div>
          </div>
        </div>
      </div>

      {idleResources.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h3 style={{ marginBottom: '1rem', color: '#c33' }}>
            <AlertTriangle size={20} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} />
            Top Idle Resources (Immediate Action Recommended)
          </h3>
          <div className="resource-table-container">
            <table className="resource-table">
              <thead>
                <tr>
                  <th>Region</th>
                  <th>Type</th>
                  <th>Name</th>
                  <th>State</th>
                  <th>Monthly Cost</th>
                  <th>CPU Utilization</th>
                  <th>Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {idleResources.slice(0, 10).map((resource, idx) => (
                  <tr key={idx}>
                    <td>{resource.region}</td>
                    <td>{resource.resource_type}</td>
                    <td>{resource.resource_name}</td>
                    <td>{resource.state}</td>
                    <td>${resource.monthly_cost_usd.toFixed(2)}</td>
                    <td>{resource.cpu_utilization_avg.toFixed(1)}%</td>
                    <td>
                      <span className={`badge ${getRecommendationBadge(resource.recommendation)}`}>
                        {resource.recommendation}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div style={{ marginTop: '2rem', padding: '1rem', background: '#f9f9f9', borderRadius: '8px' }}>
        <p style={{ fontSize: '0.9rem', color: '#666', margin: 0 }}>
          <strong>Analysis completed at:</strong> {new Date(results.timestamp).toLocaleString()}
        </p>
      </div>
    </div>
  );
}

export default Dashboard;
