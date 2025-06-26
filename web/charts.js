// ========================================
// DRONE COMPARATOR - CHARTS MODULE
// ========================================

let charts = {};

export function initializeCharts(drones) {
    console.log('Inicializando gráficos...');
    
    // Destruir gráficos existentes
    Object.values(charts).forEach(chart => {
        if (chart) chart.destroy();
    });
    
    // Crear nuevos gráficos
    createPricePerformanceChart(drones);
    createBrandDistributionChart(drones);
    createFeaturesAdoptionChart(drones);
    createPriceRangesChart(drones);
}

export function updateCharts(drones) {
    // Actualizar todos los gráficos con nuevos datos
    initializeCharts(drones);
}

// ========================================
// GRÁFICO PRECIO VS RENDIMIENTO
// ========================================

function createPricePerformanceChart(drones) {
    const ctx = document.getElementById('price-performance-chart');
    if (!ctx) return;
    
    // Preparar datos
    const data = drones
        .filter(d => d.precio && d.metrics.performance_score)
        .map(d => ({
            x: d.precio,
            y: d.metrics.performance_score,
            label: d.modelo,
            brand: d.marca
        }));
    
    // Colores por marca
    const brandColors = {
        'DJI': 'rgba(37, 99, 235, 0.6)',
        'Autel': 'rgba(124, 58, 237, 0.6)',
        'Parrot': 'rgba(16, 185, 129, 0.6)'
    };
    
    // Crear datasets por marca
    const datasets = Object.keys(brandColors).map(brand => ({
        label: brand,
        data: data.filter(d => d.brand === brand),
        backgroundColor: brandColors[brand],
        borderColor: brandColors[brand].replace('0.6', '1'),
        borderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8
    }));
    
    charts.pricePerformance = new Chart(ctx, {
        type: 'scatter',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const point = context.raw;
                            return [
                                `${point.label}`,
                                `Precio: ${point.x.toLocaleString()}`,
                                `Score: ${point.y.toFixed(1)}/100`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Precio (USD)',
                        font: { size: 14 }
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Score de Rendimiento',
                        font: { size: 14 }
                    },
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

// ========================================
// DISTRIBUCIÓN POR MARCA
// ========================================

function createBrandDistributionChart(drones) {
    const ctx = document.getElementById('brand-distribution-chart');
    if (!ctx) return;
    
    // Contar drones por marca
    const brandCounts = {};
    drones.forEach(drone => {
        brandCounts[drone.marca] = (brandCounts[drone.marca] || 0) + 1;
    });
    
    charts.brandDistribution = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(brandCounts),
            datasets: [{
                data: Object.values(brandCounts),
                backgroundColor: [
                    'rgba(37, 99, 235, 0.8)',
                    'rgba(124, 58, 237, 0.8)',
                    'rgba(16, 185, 129, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// ========================================
// ADOPCIÓN DE CARACTERÍSTICAS
// ========================================

function createFeaturesAdoptionChart(drones) {
    const ctx = document.getElementById('features-adoption-chart');
    if (!ctx) return;
    
    const features = {
        'Evita Obstáculos': d => d.features.evita_obstaculos,
        'Retorno Auto': d => d.features.retorno_automatico,
        'Seguimiento': d => d.features.seguimiento_objeto,
        'Vuelo Nocturno': d => d.features.vuelo_nocturno,
        'Modo Sport': d => d.features.modo_sport
    };
    
    const featureCounts = {};
    Object.entries(features).forEach(([name, getter]) => {
        featureCounts[name] = drones.filter(getter).length;
    });
    
    charts.featuresAdoption = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(featureCounts),
            datasets: [{
                label: 'Drones con característica',
                data: Object.values(featureCounts),
                backgroundColor: 'rgba(37, 99, 235, 0.6)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// ========================================
// RANGOS DE PRECIO
// ========================================

function createPriceRangesChart(drones) {
    const ctx = document.getElementById('price-ranges-chart');
    if (!ctx) return;
    
    const ranges = {
        '$0-500': d => d.precio <= 500,
        '$500-1500': d => d.precio > 500 && d.precio <= 1500,
        '$1500-3000': d => d.precio > 1500 && d.precio <= 3000,
        '$3000+': d => d.precio > 3000
    };
    
    const rangeCounts = {};
    Object.entries(ranges).forEach(([label, filter]) => {
        rangeCounts[label] = drones.filter(filter).length;
    });
    
    charts.priceRanges = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(rangeCounts),
            datasets: [{
                data: Object.values(rangeCounts),
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(37, 99, 235, 0.8)',
                    'rgba(124, 58, 237, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}