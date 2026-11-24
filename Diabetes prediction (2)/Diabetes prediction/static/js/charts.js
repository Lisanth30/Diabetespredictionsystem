// HealthGuard AI - Interactive Chart.js Initializations

// Color Constants
const CHART_COLORS = {
  primary: '#4f46e5',
  secondary: '#7c3aed',
  danger: '#ef4444',
  caution: '#f59e0b',
  safe: '#10b981',
  slateDark: '#0f172a',
  gridColor: 'rgba(226, 232, 240, 0.7)'
};

// 1. User Risk Trend Charts
async function initUserTrendCharts() {
  const probCanvas = document.getElementById('userProbabilityChart');
  const glucoseCanvas = document.getElementById('userGlucoseChart');
  const bmiCanvas = document.getElementById('userBmiChart');

  if (!probCanvas && !glucoseCanvas && !bmiCanvas) return;

  try {
    const response = await fetch('/api/user/trends');
    const data = await response.json();

    if (!data.labels || data.labels.length === 0) {
      const emptyMsg = document.getElementById('trendEmptyState');
      if (emptyMsg) emptyMsg.style.display = 'block';
      return;
    }

    // A. Probability Chart
    if (probCanvas) {
      new Chart(probCanvas, {
        type: 'line',
        data: {
          labels: data.labels,
          datasets: [{
            label: 'Diabetes Screening Likelihood (%)',
            data: data.probabilities,
            borderColor: CHART_COLORS.primary,
            backgroundColor: 'rgba(79, 70, 229, 0.1)',
            fill: true,
            tension: 0.35,
            pointRadius: 6,
            pointHoverRadius: 8,
            pointBackgroundColor: CHART_COLORS.primary,
            borderWidth: 3
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              grid: { color: CHART_COLORS.gridColor },
              ticks: { callback: v => v + '%' }
            },
            x: { grid: { display: false } }
          },
          plugins: {
            tooltip: {
              callbacks: {
                label: ctx => `Probability: ${ctx.parsed.y}%`
              }
            }
          }
        }
      });
    }

    // B. Glucose Chart
    if (glucoseCanvas) {
      new Chart(glucoseCanvas, {
        type: 'line',
        data: {
          labels: data.labels,
          datasets: [{
            label: 'Fasting Plasma Glucose (mg/dL)',
            data: data.glucoses,
            borderColor: CHART_COLORS.danger,
            backgroundColor: 'rgba(239, 68, 68, 0.08)',
            fill: true,
            tension: 0.35,
            pointRadius: 5,
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: false,
              grid: { color: CHART_COLORS.gridColor },
              ticks: { callback: v => v + ' mg/dL' }
            },
            x: { grid: { display: false } }
          }
        }
      });
    }

    // C. BMI Chart
    if (bmiCanvas) {
      new Chart(bmiCanvas, {
        type: 'line',
        data: {
          labels: data.labels,
          datasets: [{
            label: 'Body Mass Index (kg/m²)',
            data: data.bmis,
            borderColor: CHART_COLORS.secondary,
            backgroundColor: 'rgba(124, 58, 237, 0.08)',
            fill: true,
            tension: 0.35,
            pointRadius: 5,
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: false,
              grid: { color: CHART_COLORS.gridColor },
              ticks: { callback: v => v + ' kg/m²' }
            },
            x: { grid: { display: false } }
          }
        }
      });
    }

  } catch (err) {
    console.error('Error fetching trend data:', err);
  }
}

// 2. Admin Analytics Charts
async function initAdminAnalyticsCharts() {
  const riskCanvas = document.getElementById('adminRiskDoughnut');
  const volumeCanvas = document.getElementById('adminVolumeBar');

  if (!riskCanvas && !volumeCanvas) return;

  try {
    const response = await fetch('/api/admin/analytics');
    const data = await response.json();

    // A. Risk Distribution Doughnut
    if (riskCanvas) {
      new Chart(riskCanvas, {
        type: 'doughnut',
        data: {
          labels: ['Low Risk (<35%)', 'Medium Risk (35-65%)', 'High Risk (>65%)'],
          datasets: [{
            data: [
              data.risk_distribution.Low,
              data.risk_distribution.Medium,
              data.risk_distribution.High
            ],
            backgroundColor: [CHART_COLORS.safe, CHART_COLORS.caution, CHART_COLORS.danger],
            borderWidth: 2,
            borderColor: '#ffffff'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '70%',
          plugins: {
            legend: { position: 'bottom' }
          }
        }
      });
    }

    // B. Daily Prediction Volume
    if (volumeCanvas) {
      new Chart(volumeCanvas, {
        type: 'bar',
        data: {
          labels: data.dates,
          datasets: [{
            label: 'Screening Assessments',
            data: data.daily_counts,
            backgroundColor: 'rgba(79, 70, 229, 0.7)',
            borderColor: CHART_COLORS.primary,
            borderWidth: 1,
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              ticks: { stepSize: 1 },
              grid: { color: CHART_COLORS.gridColor }
            },
            x: { grid: { display: false } }
          }
        }
      });
    }
  } catch (err) {
    console.error('Error fetching admin analytics:', err);
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initUserTrendCharts();
  initAdminAnalyticsCharts();
});
