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
                            return '# 🚁 SISTEMA COMPLETO DE COMPARADOR DE DRONES';
                        }
                    }
                }
            }
                    }
    });