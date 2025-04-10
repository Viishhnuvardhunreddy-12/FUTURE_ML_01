document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const fileInput = document.getElementById('file');
    const downloadBtn = document.getElementById('downloadBtn');
    const alertContainer = document.getElementById('alertContainer');
    const metricsCard = document.getElementById('metricsCard');
    const metricsTable = document.getElementById('metricsTable');
    let charts = {
        forecast: null,
        yearly: null,
        weekly: null,
        monthly: null,
        quarterly: null
    };

    if (!form || !fileInput || !downloadBtn || !alertContainer) {
        console.error('Required elements not found');
        return;
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Clear any existing alerts and charts
        alertContainer.innerHTML = '';
        Object.values(charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        
        const file = fileInput.files[0];
        if (!file) {
            showAlert('Please select a file', 'danger');
            return;
        }

        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Server response was not JSON');
            }

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'An error occurred');
            }

            if (data.error) {
                showAlert(data.error, 'danger');
            } else {
                updateVisualizations(data);
                downloadBtn.style.display = 'block';
                showAlert('Forecast generated successfully!', 'success');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert(error.message || 'Error processing file', 'danger');
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Upload and Forecast';
        }
    });

    function updateVisualizations(data) {
        // Update metrics table
        updateMetrics(data.metrics);
        
        // Update main forecast chart
        updateForecastChart(data);
        
        // Update seasonality charts
        if (data.seasonality) {
            updateSeasonalityCharts(data.seasonality);
        }
    }

    function updateMetrics(metrics) {
        if (!metrics) return;
        
        metricsTable.innerHTML = Object.entries(metrics).map(([key, value]) => `
            <tr>
                <td><strong>${formatMetricName(key)}</strong></td>
                <td>${formatMetricValue(key, value)}</td>
            </tr>
        `).join('');
        
        metricsCard.style.display = 'block';
    }

    function formatMetricName(key) {
        const names = {
            'mae': 'Mean Absolute Error',
            'rmse': 'Root Mean Square Error',
            'r2': 'R² Score',
            'mape': 'Mean Absolute % Error'
        };
        return names[key] || key;
    }

    function formatMetricValue(key, value) {
        if (key === 'r2') {
            return (value * 100).toFixed(2) + '%';
        } else if (key === 'mape') {
            return value.toFixed(2) + '%';
        }
        return value.toFixed(2);
    }

    function updateForecastChart(data) {
        const ctx = document.getElementById('forecastChart').getContext('2d');
        
        if (charts.forecast) {
            charts.forecast.destroy();
        }

        const dates = data.forecast_data.map(item => new Date(item.ds).toLocaleDateString());
        const actualSales = data.original_data.map(item => parseFloat(item.y));
        const forecastedSales = data.forecast_data.map(item => parseFloat(item.yhat));
        const lowerBound = data.forecast_data.map(item => parseFloat(item.yhat_lower));
        const upperBound = data.forecast_data.map(item => parseFloat(item.yhat_upper));

        charts.forecast = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Actual Sales',
                        data: actualSales,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.1,
                        fill: false
                    },
                    {
                        label: 'Forecasted Sales',
                        data: forecastedSales,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.1,
                        fill: false
                    },
                    {
                        label: 'Upper Bound',
                        data: upperBound,
                        borderColor: 'rgba(255, 99, 132, 0.2)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        borderDash: [5, 5],
                        fill: '+1'
                    },
                    {
                        label: 'Lower Bound',
                        data: lowerBound,
                        borderColor: 'rgba(255, 99, 132, 0.2)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        borderDash: [5, 5],
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Sales'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Sales Forecast with Confidence Intervals'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
    }

    function updateSeasonalityCharts(seasonality) {
        const components = ['yearly', 'weekly', 'monthly', 'quarterly'];
        
        components.forEach(component => {
            if (seasonality[component] && seasonality[component].length > 0) {
                const ctx = document.getElementById(`${component}Chart`).getContext('2d');
                
                if (charts[component]) {
                    charts[component].destroy();
                }

                // Create appropriate labels and limit data based on the component type
                let labels = [];
                let chartData = [];
                let chartType = 'doughnut'; // Default chart type
                let chartOptions = {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: `${component.charAt(0).toUpperCase() + component.slice(1)} Pattern`
                        },
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    return `${label}: ${parseFloat(context.raw).toFixed(2)}`;
                                }
                            }
                        }
                    }
                };
                
                if (component === 'yearly') {
                    // For yearly, show only the months with significant impact
                    labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                    chartData = seasonality[component].slice(0, Math.min(12, seasonality[component].length));
                    
                    // Normalize the data
                    const absValues = chartData.map(Math.abs);
                    const maxValue = Math.max(...absValues);
                    
                    // Find the most significant months (top 6)
                    const significantIndices = Array.from(Array(chartData.length).keys())
                        .sort((a, b) => Math.abs(chartData[b]) - Math.abs(chartData[a]))
                        .slice(0, 6);
                    
                    // Create a dataset that only highlights significant months
                    const backgroundColors = labels.map((_, i) => 
                        significantIndices.includes(i) ? 
                            (chartData[i] >= 0 ? 'rgba(54, 162, 235, 0.7)' : 'rgba(255, 99, 132, 0.7)') : 
                            'rgba(201, 203, 207, 0.3)'
                    );
                    
                    chartType = 'bar';
                    chartOptions.scales = {
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: 'Impact'
                            }
                        }
                    };
                    
                } else if (component === 'weekly') {
                    // For weekly, use a compact polar area chart
                    labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
                    chartData = seasonality[component].slice(0, Math.min(7, seasonality[component].length));
                    chartType = 'polarArea';
                    
                    // Normalize data to highlight differences
                    const absValues = chartData.map(Math.abs);
                    const maxValue = Math.max(...absValues);
                    
                } else {
                    // For monthly and quarterly, use a pie chart with limited slices
                    const maxEntries = 6; // Limit to most significant entries
                    const rawData = seasonality[component];
                    
                    // Find most significant periods
                    const indices = Array.from(Array(rawData.length).keys())
                        .sort((a, b) => Math.abs(rawData[b]) - Math.abs(rawData[a]))
                        .slice(0, maxEntries);
                    
                    indices.forEach(i => {
                        // Use 1-based indexing for period numbers
                        const periodNum = i + 1;
                        labels.push(`Period ${periodNum}`);
                        chartData.push(Math.abs(rawData[i])); // Use absolute values for pie chart
                    });
                    
                    chartType = 'pie';
                }
                
                // Convert negative values to absolute for some chart types
                if (chartType === 'pie' || chartType === 'polarArea' || chartType === 'doughnut') {
                    chartData = chartData.map(Math.abs);
                }
                
                // Generate colors based on the data values
                const backgroundColors = chartData.map((value, i) => {
                    if (chartType === 'bar') {
                        return value >= 0 ? 'rgba(54, 162, 235, 0.7)' : 'rgba(255, 99, 132, 0.7)';
                    } else {
                        const hue = (i * 360 / chartData.length) % 360;
                        return `hsla(${hue}, 70%, 60%, 0.7)`;
                    }
                });
                
                // Create the chart
                charts[component] = new Chart(ctx, {
                    type: chartType,
                    data: {
                        labels: labels,
                        datasets: [{
                            label: `${component.charAt(0).toUpperCase() + component.slice(1)} Pattern`,
                            data: chartData,
                            backgroundColor: backgroundColors,
                            borderColor: backgroundColors.map(color => color.replace('0.7', '1')),
                            borderWidth: 1
                        }]
                    },
                    options: chartOptions
                });
            }
        });
    }

    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Clear existing alerts
        alertContainer.innerHTML = '';
        alertContainer.appendChild(alertDiv);
        
        // Auto-dismiss success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                if (alertDiv.parentNode === alertContainer) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }
}); 