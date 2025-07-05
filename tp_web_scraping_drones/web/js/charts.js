// Gráficos Chart.js configurados dinámicamente

class DroneCharts {
    constructor() {
        this.charts = {};
        this.initializeCharts();
    }

    initializeCharts() {
        // Configuración por defecto para todos los gráficos
        Chart.defaults.color = getComputedStyle(document.body).getPropertyValue('--text-color');
        Chart.defaults.borderColor = getComputedStyle(document.body).getPropertyValue('--border-color');
        Chart.defaults.backgroundColor = getComputedStyle(document.body).getPropertyValue('--card-bg');
    }

    createPriceComparisonChart(drones) {
        const ctx = document.getElementById('priceChart')?.getContext('2d');
        if (!ctx) return;

        // Destruir gráfico existente
        if (this.charts.priceChart) {
            this.charts.priceChart.destroy();
        }

        const data = drones.map(drone => ({
            x: drone.especificaciones_tecnicas.peso_gramos || 0,
            y: drone.especificaciones_tecnicas.vuelo_minutos || 0,
            label: drone.modelo,
            brand: drone.marca
        }));

        const brandColors = {
            'DJI': '#FF6B6B',
            'Autel Robotics': '#4ECDC4',
            'Parrot': '#45B7D1'
        };

        this.charts.priceChart = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: Object.entries(brandColors).map(([brand, color]) => ({
                    label: brand,
                    data: data.filter(d => d.brand === brand),
                    backgroundColor: color + '80',
                    borderColor: color,
                    borderWidth: 2,
                    pointRadius: 8,
                    pointHoverRadius: 10
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        title: {
                            display: true,
                            text: 'Peso (gramos)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString() + 'g';
                            }
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Tiempo de Vuelo (min)'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const point = context.raw;
                                return `${point.label}: ${point.x.toLocaleString()}g - ${point.y}min`;
                            }
                        }
                    },
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
    }

    createSpecRadarChart(drone) {
        const ctx = document.getElementById('radarChart')?.getContext('2d');
        if (!ctx) return;

        if (this.charts.radarChart) {
            this.charts.radarChart.destroy();
        }

        const specs = drone.specifications;
        const normalizedData = [
            this.normalizeValue(specs.flight_time, 0, 60),
            this.normalizeValue(specs.max_speed, 0, 100),
            this.normalizeValue(specs.max_range, 0, 20000),
            this.normalizeValue(specs.camera_resolution?.split('x')[0] || 0, 0, 8000),
            this.normalizeValue(specs.max_altitude, 0, 10000),
            this.normalizeValue(specs.wind_resistance, 0, 15),
            100 - this.normalizeValue(specs.weight, 0, 5000) // Invertido: menos peso es mejor
        ];

        this.charts.radarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: [
                    'Tiempo de Vuelo',
                    'Velocidad Máx.',
                    'Alcance Máx.',
                    'Resolución Cámara',
                    'Altitud Máx.',
                    'Resistencia Viento',
                    'Portabilidad'
                ],
                datasets: [{
                    label: drone.model,
                    data: normalizedData,
                    backgroundColor: drone.brand === 'DJI' ? '#FF6B6B40' : 
                                   drone.brand === 'Autel Robotics' ? '#4ECDC440' : '#45B7D140',
                    borderColor: drone.brand === 'DJI' ? '#FF6B6B' : 
                               drone.brand === 'Autel Robotics' ? '#4ECDC4' : '#45B7D1',
                    borderWidth: 2,
                    pointBackgroundColor: drone.brand === 'DJI' ? '#FF6B6B' : 
                                        drone.brand === 'Autel Robotics' ? '#4ECDC4' : '#45B7D1',
                    pointBorderColor: '#fff',
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
    }

    createBrandDistributionChart(drones) {
        const ctx = document.getElementById('brandChart')?.getContext('2d');
        if (!ctx) return;

        if (this.charts.brandChart) {
            this.charts.brandChart.destroy();
        }

        const brandCounts = drones.reduce((acc, drone) => {
            acc[drone.brand] = (acc[drone.brand] || 0) + 1;
            return acc;
        }, {});

        const brandColors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA726', '#AB47BC'];

        this.charts.brandChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(brandCounts),
                datasets: [{
                    data: Object.values(brandCounts),
                    backgroundColor: brandColors.slice(0, Object.keys(brandCounts).length),
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.raw / total) * 100).toFixed(1);
                                return `${context.label}: ${context.raw} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    createFeatureComparisonChart(drones, features) {
        const ctx = document.getElementById('featureChart')?.getContext('2d');
        if (!ctx) return;

        if (this.charts.featureChart) {
            this.charts.featureChart.destroy();
        }

        const brandColors = {
            'DJI': '#FF6B6B',
            'Autel Robotics': '#4ECDC4',
            'Parrot': '#45B7D1'
        };

        const datasets = Object.keys(brandColors).map(brand => {
            const brandDrones = drones.filter(d => d.brand === brand);
            const avgFeatures = features.map(feature => {
                const values = brandDrones
                    .map(d => this.getFeatureValue(d.specifications, feature))
                    .filter(v => v !== null && v !== undefined);
                return values.length > 0 ? values.reduce((a, b) => a + b) / values.length : 0;
            });

            return {
                label: brand,
                data: avgFeatures,
                backgroundColor: brandColors[brand] + '40',
                borderColor: brandColors[brand],
                borderWidth: 2,
                tension: 0.4
            };
        });

        this.charts.featureChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: features.map(f => this.getFeatureLabel(f)),
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Valor Normalizado'
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
    }

    normalizeValue(value, min, max) {
        if (value === null || value === undefined) return 0;
        const numValue = typeof value === 'string' ? parseFloat(value) : value;
        if (isNaN(numValue)) return 0;
        return Math.min(100, Math.max(0, ((numValue - min) / (max - min)) * 100));
    }

    getFeatureValue(specs, feature) {
        switch (feature) {
            case 'flight_time':
                return specs.flight_time || 0;
            case 'max_speed':
                return specs.max_speed || 0;
            case 'max_range':
                return specs.max_range || 0;
            case 'camera_resolution':
                return specs.camera_resolution ? parseInt(specs.camera_resolution.split('x')[0]) : 0;
            case 'max_altitude':
                return specs.max_altitude || 0;
            case 'wind_resistance':
                return specs.wind_resistance || 0;
            case 'weight':
                return 5000 - (specs.weight || 0); // Invertido
            default:
                return 0;
        }
    }

    getFeatureLabel(feature) {
        const labels = {
            'flight_time': 'Tiempo Vuelo',
            'max_speed': 'Velocidad',
            'max_range': 'Alcance',
            'camera_resolution': 'Resolución',
            'max_altitude': 'Altitud',
            'wind_resistance': 'Resist. Viento',
            'weight': 'Portabilidad'
        };
        return labels[feature] || feature;
    }

    updateCharts(drones, selectedDrone = null) {
        if (drones.length === 0) return;

        // Actualizar gráfico de precios
        this.createPriceComparisonChart(drones);

        // Actualizar distribución de marcas
        this.createBrandDistributionChart(drones);

        // Actualizar comparación de características
        const features = ['flight_time', 'max_speed', 'max_range', 'camera_resolution'];
        this.createFeatureComparisonChart(drones, features);

        // Actualizar radar si hay un drone seleccionado
        if (selectedDrone) {
            this.createSpecRadarChart(selectedDrone);
        }
    }

    destroyAllCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.charts = {};
    }

    // Método para actualizar colores cuando cambia el tema
    updateTheme() {
        const textColor = getComputedStyle(document.body).getPropertyValue('--text-color');
        const borderColor = getComputedStyle(document.body).getPropertyValue('--border-color');

        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.options.scales.x.ticks.color = textColor;
                chart.options.scales.y.ticks.color = textColor;
                chart.options.plugins.legend.labels.color = textColor;
                chart.update();
            }
        });
    }
}

// Inicializar cuando el DOM esté listo
let droneCharts;
document.addEventListener('DOMContentLoaded', () => {
    droneCharts = new DroneCharts();
});

// Exportar para uso en otros módulos
window.DroneCharts = DroneCharts;