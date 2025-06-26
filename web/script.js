// ========================================
// DRONE COMPARATOR - MAIN SCRIPT
// ========================================

import { initializeFilters, applyFilters } from './filters.js';
import { initializeCharts, updateCharts } from './charts.js';

// Estado global de la aplicación
const appState = {
    allDrones: [],
    filteredDrones: [],
    selectedDrones: new Set(),
    currentPage: 1,
    itemsPerPage: 12,
    sortBy: 'price_asc',
    currentSection: 'comparator',
    wizardData: {
        budget: null,
        experience: null,
        use: null,
        features: []
    }
};

// ========================================
// INICIALIZACIÓN
// ========================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('Inicializando DroneMatch Pro...');
    
    // Mostrar loading
    showLoading();
    
    try {
        // Cargar datos
        await loadDroneData();
        
        // Inicializar componentes
        initializeNavigation();
        initializeFilters(appState);
        initializeSort();
        initializeComparison();
        initializeWizard();
        initializeModals();
        
        // Renderizar vista inicial
        renderDrones();
        
        // Inicializar gráficos si estamos en la sección de insights
        if (appState.currentSection === 'insights') {
            initializeCharts(appState.allDrones);
        }
        
    } catch (error) {
        console.error('Error inicializando la aplicación:', error);
        showError('Error cargando los datos. Por favor, recarga la página.');
    } finally {
        hideLoading();
    }
});

// ========================================
// CARGA DE DATOS
// ========================================

async function loadDroneData() {
    try {
        const response = await fetch('../analysis/solution_data.json');
        if (!response.ok) {
            throw new Error('Error cargando datos');
        }
        
        const data = await response.json();
        appState.allDrones = data.drones;
        appState.filteredDrones = [...data.drones];
        
        console.log(`Cargados ${appState.allDrones.length} drones`);
        
        // Guardar metadata y insights globalmente
        window.droneData = data;
        
    } catch (error) {
        console.error('Error cargando datos:', error);
        // Usar datos de ejemplo si falla la carga
        appState.allDrones = generateSampleData();
        appState.filteredDrones = [...appState.allDrones];
    }
}

// ========================================
// NAVEGACIÓN
// ========================================

function initializeNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    
    navButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const section = e.currentTarget.dataset.section;
            switchSection(section);
        });
    });
}

function switchSection(section) {
    // Actualizar estado
    appState.currentSection = section;
    
    // Actualizar botones de navegación
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.section === section);
    });
    
    // Ocultar todas las secciones
    document.getElementById('filters-panel').style.display = 'none';
    document.getElementById('results-grid').style.display = 'none';
    document.getElementById('detailed-comparison').style.display = 'none';
    document.getElementById('market-insights').style.display = 'none';
    document.getElementById('recommendations-section').style.display = 'none';
    
    // Mostrar sección activa
    switch (section) {
        case 'comparator':
            document.getElementById('filters-panel').style.display = 'block';
            document.getElementById('results-grid').style.display = 'block';
            if (appState.selectedDrones.size > 0) {
                document.getElementById('detailed-comparison').style.display = 'block';
            }
            break;
            
        case 'insights':
            document.getElementById('market-insights').style.display = 'block';
            initializeCharts(appState.allDrones);
            loadInsights();
            break;
            
        case 'recommendations':
            document.getElementById('recommendations-section').style.display = 'block';
            resetWizard();
            break;
    }
}

// ========================================
// RENDERIZADO DE DRONES
// ========================================

function renderDrones() {
    const droneGrid = document.getElementById('drone-grid');
    const startIndex = (appState.currentPage - 1) * appState.itemsPerPage;
    const endIndex = startIndex + appState.itemsPerPage;
    
    // Ordenar drones
    const sortedDrones = sortDrones(appState.filteredDrones);
    
    // Obtener página actual
    const pageDrones = sortedDrones.slice(startIndex, endIndex);
    
    // Limpiar grid
    droneGrid.innerHTML = '';
    
    // Renderizar cada drone
    pageDrones.forEach(drone => {
        const droneCard = createDroneCard(drone);
        droneGrid.appendChild(droneCard);
    });
    
    // Actualizar contador
    updateResultsCount();
    
    // Renderizar paginación
    renderPagination(sortedDrones.length);
}

function createDroneCard(drone) {
    const card = document.createElement('div');
    card.className = 'drone-card fade-in';
    card.dataset.droneId = drone.id;
    
    // Determinar badges
    const badges = [];
    if (drone.metrics.price_performance_ratio > 5) {
        badges.push('<span class="drone-badge best-value">Mejor Valor</span>');
    }
    if (drone.clasificacion.nivel === 'principiante') {
        badges.push('<span class="drone-badge">Principiante</span>');
    }
    
    // Crear HTML del card
    card.innerHTML = `
        <div class="drone-card-header">
            ${badges.join('')}
            <img src="${drone.imagen}" alt="${drone.modelo}" class="drone-image" 
                 onerror="this.src='/assets/drone_icons/generic.png'">
        </div>
        <div class="drone-card-body">
            <h3 class="drone-title">${drone.modelo}</h3>
            <p class="drone-brand">${drone.marca}</p>
            <p class="drone-price">${formatPrice(drone.precio)}</p>
            
            <div class="drone-specs">
                <div class="spec-item">
                    <i class="fas fa-clock"></i>
                    <span><strong>${drone.specs.autonomia || 'N/A'}</strong> min</span>
                </div>
                <div class="spec-item">
                    <i class="fas fa-broadcast-tower"></i>
                    <span><strong>${formatDistance(drone.specs.alcance)}</strong></span>
                </div>
                <div class="spec-item">
                    <i class="fas fa-weight"></i>
                    <span><strong>${drone.specs.peso || 'N/A'}</strong>g</span>
                </div>
                <div class="spec-item">
                    <i class="fas fa-video"></i>
                    <span><strong>${drone.camara.resolucion || 'N/A'}</strong></span>
                </div>
            </div>
            
            <div class="drone-features">
                ${renderFeatureTags(drone.features)}
            </div>
            
            <div class="drone-actions">
                <button class="btn-compare ${appState.selectedDrones.has(drone.id) ? 'selected' : ''}" 
                        onclick="toggleComparison(${drone.id})">
                    <i class="fas fa-exchange-alt"></i>
                    ${appState.selectedDrones.has(drone.id) ? 'Seleccionado' : 'Comparar'}
                </button>
                <button class="btn-details" onclick="showDroneDetails(${drone.id})">
                    <i class="fas fa-info-circle"></i>
                    Detalles
                </button>
            </div>
        </div>
    `;
    
    return card;
}

function renderFeatureTags(features) {
    const featureIcons = {
        evita_obstaculos: { icon: 'shield-alt', label: 'Evita Obstáculos' },
        retorno_automatico: { icon: 'home', label: 'Retorno Auto' },
        seguimiento_objeto: { icon: 'crosshairs', label: 'Seguimiento' },
        vuelo_nocturno: { icon: 'moon', label: 'Nocturno' },
        modo_sport: { icon: 'tachometer-alt', label: 'Sport' }
    };
    
    return Object.entries(features)
        .filter(([key, value]) => value && featureIcons[key])
        .map(([key]) => `
            <span class="feature-tag active">
                <i class="fas fa-${featureIcons[key].icon}"></i>
                ${featureIcons[key].label}
            </span>
        `)
        .join('');
}

// ========================================
// ORDENAMIENTO
// ========================================

function initializeSort() {
    const sortSelect = document.getElementById('sort-select');
    
    sortSelect.addEventListener('change', (e) => {
        appState.sortBy = e.target.value;
        appState.currentPage = 1;
        renderDrones();
    });
}

function sortDrones(drones) {
    const sorted = [...drones];
    
    switch (appState.sortBy) {
        case 'price_asc':
            sorted.sort((a, b) => (a.precio || 0) - (b.precio || 0));
            break;
        case 'price_desc':
            sorted.sort((a, b) => (b.precio || 0) - (a.precio || 0));
            break;
        case 'performance':
            sorted.sort((a, b) => (b.metrics.performance_score || 0) - (a.metrics.performance_score || 0));
            break;
        case 'value':
            sorted.sort((a, b) => (b.metrics.price_performance_ratio || 0) - (a.metrics.price_performance_ratio || 0));
            break;
        case 'autonomy':
            sorted.sort((a, b) => (b.specs.autonomia || 0) - (a.specs.autonomia || 0));
            break;
        case 'range':
            sorted.sort((a, b) => (b.specs.alcance || 0) - (a.specs.alcance || 0));
            break;
    }
    
    return sorted;
}

// ========================================
// PAGINACIÓN
// ========================================

function renderPagination(totalItems) {
    const pagination = document.getElementById('pagination');
    const totalPages = Math.ceil(totalItems / appState.itemsPerPage);
    
    pagination.innerHTML = '';
    
    // Botón anterior
    const prevBtn = document.createElement('button');
    prevBtn.className = 'page-btn';
    prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
    prevBtn.disabled = appState.currentPage === 1;
    prevBtn.onclick = () => changePage(appState.currentPage - 1);
    pagination.appendChild(prevBtn);
    
    // Páginas
    const maxVisiblePages = 5;
    let startPage = Math.max(1, appState.currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage < maxVisiblePages - 1) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `page-btn ${i === appState.currentPage ? 'active' : ''}`;
        pageBtn.textContent = i;
        pageBtn.onclick = () => changePage(i);
        pagination.appendChild(pageBtn);
    }
    
    // Botón siguiente
    const nextBtn = document.createElement('button');
    nextBtn.className = 'page-btn';
    nextBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
    nextBtn.disabled = appState.currentPage === totalPages;
    nextBtn.onclick = () => changePage(appState.currentPage + 1);
    pagination.appendChild(nextBtn);
}

function changePage(page) {
    appState.currentPage = page;
    renderDrones();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ========================================
// COMPARACIÓN
// ========================================

function initializeComparison() {
    document.getElementById('clear-comparison').addEventListener('click', clearComparison);
}

window.toggleComparison = function(droneId) {
    if (appState.selectedDrones.has(droneId)) {
        appState.selectedDrones.delete(droneId);
    } else {
        if (appState.selectedDrones.size >= 5) {
            showNotification('Máximo 5 drones para comparar', 'warning');
            return;
        }
        appState.selectedDrones.add(droneId);
    }
    
    updateComparisonUI();
    renderDrones();
};

function updateComparisonUI() {
    const comparisonSection = document.getElementById('detailed-comparison');
    
    if (appState.selectedDrones.size > 0) {
        comparisonSection.style.display = 'block';
        renderComparisonTable();
    } else {
        comparisonSection.style.display = 'none';
    }
}

function renderComparisonTable() {
    const table = document.getElementById('comparison-table');
    const selectedDronesArray = Array.from(appState.selectedDrones)
        .map(id => appState.allDrones.find(d => d.id === id))
        .filter(Boolean);
    
    if (selectedDronesArray.length === 0) return;
    
    let html = '<table><thead><tr><th>Característica</th>';
    
    // Headers con imágenes
    selectedDronesArray.forEach(drone => {
        html += `
            <th class="comparison-drone-header">
                <img src="${drone.imagen}" alt="${drone.modelo}" class="comparison-drone-image"
                     onerror="this.src='/assets/drone_icons/generic.png'">
                <div class="comparison-drone-name">${drone.modelo}</div>
                <div class="comparison-drone-price">${formatPrice(drone.precio)}</div>
            </th>
        `;
    });
    
    html += '</tr></thead><tbody>';
    
    // Filas de comparación
    const comparisonRows = [
        { label: 'Marca', getValue: d => d.marca },
        { label: 'Categoría', getValue: d => d.clasificacion.categoria },
        { label: 'Nivel Usuario', getValue: d => d.clasificacion.nivel },
        { label: 'Peso', getValue: d => `${d.specs.peso || 'N/A'}g`, compare: 'lower' },
        { label: 'Autonomía', getValue: d => `${d.specs.autonomia || 'N/A'} min`, compare: 'higher' },
        { label: 'Alcance', getValue: d => formatDistance(d.specs.alcance), compare: 'higher' },
        { label: 'Velocidad Máx', getValue: d => `${d.specs.velocidad || 'N/A'} km/h`, compare: 'higher' },
        { label: 'Cámara', getValue: d => d.camara.resolucion || 'N/A' },
        { label: 'FPS Máx', getValue: d => `${d.camara.fps || 'N/A'} fps` },
        { label: 'Estabilización', getValue: d => d.camara.estabilizacion || 'N/A' },
        { label: 'Evita Obstáculos', getValue: d => d.features.evita_obstaculos ? '✓' : '✗', isBoolean: true },
        { label: 'Retorno Auto', getValue: d => d.features.retorno_automatico ? '✓' : '✗', isBoolean: true },
        { label: 'Seguimiento', getValue: d => d.features.seguimiento_objeto ? '✓' : '✗', isBoolean: true },
        { label: 'Vuelo Nocturno', getValue: d => d.features.vuelo_nocturno ? '✓' : '✗', isBoolean: true },
        { label: 'Modo Sport', getValue: d => d.features.modo_sport ? '✓' : '✗', isBoolean: true },
        { label: 'Score Rendimiento', getValue: d => `${Math.round(d.metrics.performance_score || 0)}/100`, compare: 'higher' },
        { label: 'Ratio Precio/Valor', getValue: d => (d.metrics.price_performance_ratio || 0).toFixed(2), compare: 'higher' }
    ];
    
    comparisonRows.forEach(row => {
        html += `<tr><td><strong>${row.label}</strong></td>`;
        
        const values = selectedDronesArray.map(d => ({
            drone: d,
            value: row.getValue(d),
            numeric: parseFloat(row.getValue(d)) || 0
        }));
        
        // Encontrar mejor valor si es comparable
        let bestValue = null;
        if (row.compare) {
            if (row.compare === 'higher') {
                bestValue = Math.max(...values.map(v => v.numeric));
            } else if (row.compare === 'lower') {
                bestValue = Math.min(...values.filter(v => v.numeric > 0).map(v => v.numeric));
            }
        }
        
        values.forEach(({ value, numeric }) => {
            const isBest = row.compare && numeric === bestValue && bestValue > 0;
            const classNames = ['comparison-value'];
            if (isBest) classNames.push('best');
            
            if (row.isBoolean) {
                html += `<td class="${classNames.join(' ')}">
                    <span class="${value === '✓' ? 'feature-yes' : 'feature-no'}">${value}</span>
                </td>`;
            } else {
                html += `<td class="${classNames.join(' ')}">${value}</td>`;
            }
        });
        
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    table.innerHTML = html;
}

function clearComparison() {
    appState.selectedDrones.clear();
    updateComparisonUI();
    renderDrones();
}

// ========================================
// RECOMENDADOR (WIZARD)
// ========================================

function initializeWizard() {
    const wizardNext = document.getElementById('wizard-next');
    const wizardPrev = document.getElementById('wizard-prev');
    const wizardFinish = document.getElementById('wizard-finish');
    
    wizardNext.addEventListener('click', nextWizardStep);
    wizardPrev.addEventListener('click', prevWizardStep);
    wizardFinish.addEventListener('click', finishWizard);
    
    // Event listeners para opciones
    document.querySelectorAll('.budget-option').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.budget-option').forEach(b => b.classList.remove('selected'));
            e.currentTarget.classList.add('selected');
            appState.wizardData.budget = parseInt(e.currentTarget.dataset.budget);
        });
    });
    
    document.querySelectorAll('.experience-option').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.experience-option').forEach(b => b.classList.remove('selected'));
            e.currentTarget.classList.add('selected');
            appState.wizardData.experience = e.currentTarget.dataset.level;
        });
    });
    
    document.querySelectorAll('.use-option').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.use-option').forEach(b => b.classList.remove('selected'));
            e.currentTarget.classList.add('selected');
            appState.wizardData.use = e.currentTarget.dataset.use;
        });
    });
}

function getCurrentWizardStep() {
    return document.querySelector('.wizard-panel.active').dataset.panel;
}

function nextWizardStep() {
    const currentStep = parseInt(getCurrentWizardStep());
    
    // Validar paso actual
    if (!validateWizardStep(currentStep)) {
        return;
    }
    
    if (currentStep < 4) {
        showWizardStep(currentStep + 1);
    }
}

function prevWizardStep() {
    const currentStep = parseInt(getCurrentWizardStep());
    
    if (currentStep > 1) {
        showWizardStep(currentStep - 1);
    }
}

function showWizardStep(step) {
    // Actualizar paneles
    document.querySelectorAll('.wizard-panel').forEach(panel => {
        panel.classList.toggle('active', panel.dataset.panel === step.toString());
    });
    
    // Actualizar indicadores de pasos
    document.querySelectorAll('.wizard-step').forEach((stepEl, index) => {
        const stepNum = index + 1;
        stepEl.classList.toggle('active', stepNum === step);
        stepEl.classList.toggle('completed', stepNum < step);
    });
    
    // Actualizar botones de navegación
    document.getElementById('wizard-prev').style.display = step === 1 ? 'none' : 'block';
    document.getElementById('wizard-next').style.display = step === 4 ? 'none' : 'block';
    document.getElementById('wizard-finish').style.display = step === 4 ? 'block' : 'none';
}

function validateWizardStep(step) {
    switch (step) {
        case 1:
            if (!appState.wizardData.budget) {
                showNotification('Por favor selecciona un presupuesto', 'warning');
                return false;
            }
            break;
        case 2:
            if (!appState.wizardData.experience) {
                showNotification('Por favor selecciona tu nivel de experiencia', 'warning');
                return false;
            }
            break;
        case 3:
            if (!appState.wizardData.use) {
                showNotification('Por favor selecciona el uso principal', 'warning');
                return false;
            }
            break;
    }
    return true;
}

function finishWizard() {
    // Recopilar características seleccionadas
    appState.wizardData.features = Array.from(
        document.querySelectorAll('.feature-option input:checked')
    ).map(input => input.value);
    
    // Generar recomendaciones
    const recommendations = generateRecommendations();
    
    // Mostrar resultados
    showRecommendations(recommendations);
}

function generateRecommendations() {
    const { budget, experience, use, features } = appState.wizardData;
    
    // Filtrar drones por presupuesto
    let candidates = appState.allDrones.filter(drone => drone.precio <= budget);
    
    // Filtrar por nivel de experiencia
    const experienceLevels = {
        'principiante': ['principiante', 'intermedio'],
        'intermedio': ['intermedio', 'avanzado'],
        'avanzado': ['intermedio', 'avanzado', 'profesional'],
        'profesional': ['avanzado', 'profesional']
    };
    
    candidates = candidates.filter(drone => 
        experienceLevels[experience].includes(drone.clasificacion.nivel)
    );
    
    // Filtrar por uso principal
    if (use !== 'recreativo') {
        candidates = candidates.filter(drone =>
            drone.clasificacion.usos.includes(use)
        );
    }
    
    // Puntuar según características requeridas
    candidates.forEach(drone => {
        let score = 0;
        
        // Score base por precio (menor precio = mayor score)
        score += (1 - drone.precio / budget) * 20;
        
        // Score por características
        features.forEach(feature => {
            if (feature === 'camara_4k' && ['4K', '6K', '8K'].includes(drone.camara.resolucion)) {
                score += 15;
            } else if (drone.features[feature]) {
                score += 10;
            }
        });
        
        // Score por métricas
        score += (drone.metrics.performance_score || 0) * 0.3;
        score += (drone.metrics.price_performance_ratio || 0) * 5;
        
        // Ajustes por caso de uso
        switch (use) {
            case 'fotografia':
            case 'video_profesional':
                if (['4K', '6K', '8K'].includes(drone.camara.resolucion)) {
                    score += 20;
                }
                if (drone.camara.estabilizacion === 'mecanica') {
                    score += 10;
                }
                break;
            case 'viajes':
                if (drone.specs.peso < 500) {
                    score += 15;
                }
                break;
            case 'inspeccion':
                if (drone.specs.alcance > 5000) {
                    score += 15;
                }
                if (drone.specs.autonomia > 30) {
                    score += 10;
                }
                break;
        }
        
        drone.recommendationScore = score;
    });
    
    // Ordenar por score y tomar top 5
    candidates.sort((a, b) => b.recommendationScore - a.recommendationScore);
    
    return candidates.slice(0, 5).map((drone, index) => ({
        rank: index + 1,
        drone: drone,
        score: drone.recommendationScore,
        reasons: generateReasons(drone, { budget, experience, use, features })
    }));
}

function generateReasons(drone, profile) {
    const reasons = [];
    
    // Razón por precio
    if (drone.precio < profile.budget * 0.7) {
        reasons.push('Excelente precio dentro de tu presupuesto');
    }
    
    // Razón por rendimiento
    if (drone.metrics.price_performance_ratio > 5) {
        reasons.push('Excepcional relación precio/rendimiento');
    }
    
    // Razón por características
    const matchedFeatures = profile.features.filter(f => {
        if (f === 'camara_4k') {
            return ['4K', '6K', '8K'].includes(drone.camara.resolucion);
        }
        return drone.features[f];
    });
    
    if (matchedFeatures.length >= 3) {
        reasons.push(`Incluye ${matchedFeatures.length} de tus características deseadas`);
    }
    
    // Razones específicas por uso
    switch (profile.use) {
        case 'fotografia':
            if (['6K', '8K'].includes(drone.camara.resolucion)) {
                reasons.push(`Cámara profesional ${drone.camara.resolucion}`);
            }
            break;
        case 'viajes':
            if (drone.specs.peso < 400) {
                reasons.push('Ultra portátil para viajar');
            }
            break;
        case 'inspeccion':
            if (drone.specs.autonomia > 35) {
                reasons.push(`Gran autonomía de ${drone.specs.autonomia} minutos`);
            }
            break;
    }
    
    return reasons;
}

function showRecommendations(recommendations) {
    const resultsContainer = document.getElementById('recommendation-results');
    const dronesContainer = document.getElementById('recommended-drones');
    
    // Ocultar wizard
    document.querySelector('.recommendation-wizard').style.display = 'none';
    
    // Mostrar resultados
    resultsContainer.style.display = 'block';
    
    // Limpiar contenedor
    dronesContainer.innerHTML = '';
    
    // Renderizar recomendaciones
    recommendations.forEach(({ rank, drone, score, reasons }) => {
        const rankClass = rank === 1 ? 'gold' : rank === 2 ? 'silver' : rank === 3 ? 'bronze' : '';
        
        const card = document.createElement('div');
        card.className = 'recommendation-card slide-up';
        card.innerHTML = `
            <div class="recommendation-rank ${rankClass}">${rank}</div>
            
            <div class="recommendation-details">
                <h5>${drone.modelo}</h5>
                <p class="recommendation-brand">${drone.marca}</p>
                
                <ul class="recommendation-reasons">
                    ${reasons.map(r => `<li>${r}</li>`).join('')}
                </ul>
                
                <div class="recommendation-specs">
                    <span class="rec-spec">
                        <i class="fas fa-clock"></i>
                        ${drone.specs.autonomia} min
                    </span>
                    <span class="rec-spec">
                        <i class="fas fa-broadcast-tower"></i>
                        ${formatDistance(drone.specs.alcance)}
                    </span>
                    <span class="rec-spec">
                        <i class="fas fa-video"></i>
                        ${drone.camara.resolucion}
                    </span>
                </div>
            </div>
            
            <div class="recommendation-price">
                <p class="rec-price-label">Precio</p>
                <p class="rec-price-value">${formatPrice(drone.precio)}</p>
                <div class="recommendation-score">Score: ${Math.round(score)}</div>
            </div>
        `;
        
        card.addEventListener('click', () => showDroneDetails(drone.id));
        dronesContainer.appendChild(card);
    });
}

function resetWizard() {
    // Resetear datos
    appState.wizardData = {
        budget: null,
        experience: null,
        use: null,
        features: []
    };
    
    // Resetear UI
    document.querySelectorAll('.selected').forEach(el => el.classList.remove('selected'));
    document.querySelectorAll('.feature-option input').forEach(input => input.checked = false);
    
    // Mostrar wizard y ocultar resultados
    document.querySelector('.recommendation-wizard').style.display = 'block';
    document.getElementById('recommendation-results').style.display = 'none';
    
    // Ir al paso 1
    showWizardStep(1);
}

// ========================================
// MODALES
// ========================================

function initializeModals() {
    const modal = document.getElementById('drone-detail-modal');
    const closeBtn = modal.querySelector('.modal-close');
    
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

window.showDroneDetails = function(droneId) {
    const drone = appState.allDrones.find(d => d.id === droneId);
    if (!drone) return;
    
    const modal = document.getElementById('drone-detail-modal');
    const content = document.getElementById('drone-detail-content');
    
    content.innerHTML = `
        <div class="detail-header">
            <img src="${drone.imagen}" alt="${drone.modelo}" class="detail-image"
                 onerror="this.src='/assets/drone_icons/generic.png'">
            
            <div class="detail-info">
                <h2>${drone.modelo}</h2>
                <p class="detail-brand">${drone.marca}</p>
                <p class="detail-price">${formatPrice(drone.precio)}</p>
                
                <div class="detail-badges">
                    <span class="detail-badge primary">
                        <i class="fas fa-layer-group"></i>
                        ${drone.clasificacion.categoria}
                    </span>
                    <span class="detail-badge">
                        <i class="fas fa-user"></i>
                        ${drone.clasificacion.nivel}
                    </span>
                    ${drone.clasificacion.usos.map(uso => `
                        <span class="detail-badge">
                            <i class="fas fa-tag"></i>
                            ${uso}
                        </span>
                    `).join('')}
                </div>
            </div>
        </div>
        
        <div class="detail-tabs">
            <div class="tab-list">
                <button class="tab-button active" onclick="showTab('specs')">
                    Especificaciones
                </button>
                <button class="tab-button" onclick="showTab('camera')">
                    Cámara
                </button>
                <button class="tab-button" onclick="showTab('features')">
                    Características
                </button>
                <button class="tab-button" onclick="showTab('metrics')">
                    Métricas
                </button>
            </div>
        </div>
        
        <div class="tab-content active" id="specs-tab">
            <div class="specs-grid">
                <div class="spec-group">
                    <h4><i class="fas fa-cog"></i> Especificaciones Técnicas</h4>
                    <div class="spec-list">
                        <div class="spec-row">
                            <span class="spec-label">Peso</span>
                            <span class="spec-value">${drone.specs.peso || 'N/A'}g</span>
                        </div>
                        <div class="spec-row">
                            <span class="spec-label">Autonomía</span>
                            <span class="spec-value">${drone.specs.autonomia || 'N/A'} minutos</span>
                        </div>
                        <div class="spec-row">
                            <span class="spec-label">Alcance</span>
                            <span class="spec-value">${formatDistance(drone.specs.alcance)}</span>
                        </div>
                        <div class="spec-row">
                            <span class="spec-label">Velocidad Máxima</span>
                            <span class="spec-value">${drone.specs.velocidad || 'N/A'} km/h</span>
                        </div>
                        <div class="spec-row">
                            <span class="spec-label">Resistencia al Viento</span>
                            <span class="spec-value">${drone.specs.resistencia_viento || 'N/A'}</span>
                        </div>
                        <div class="spec-row">
                            <span class="spec-label">Temperatura de Operación</span>
                            <span class="spec-value">${drone.specs.temperatura || 'N/A'}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="tab-content" id="camera-tab">
            <div class="specs-grid">
                <div class="spec-group">
                    <h4><i class="fas fa-camera"></i> Especificaciones de Cámara</h4>
                    <div class="spec-list">
                        <div class="spec-row">
                            <span class="spec-label">Resolución de Video</span>
                            <span class="spec-value">${drone.camara.resolucion || 'N/A'}</span>
                        </div>
                        <div class="spec-row">
                            <span class="spec-label">FPS Máximo</span>
                            <span class="spec-value">${drone.camara.fps || 'N/A'} fps</span>
                        </div>
                        <div class="spec-row">
                            <span class="spec-label">Sensor</span>
                            <span class="spec-value">${drone.camara.sensor || 'N/A'}</span>
                        </div>
                        <div class="spec-row">
                            <span class="spec-label">Estabilización</span>
                            <span class="spec-value">${drone.camara.estabilizacion || 'N/A'}</span>
                        </div>
                        <div class="spec-row">
                            <span class="spec-label">Zoom Óptico</span>
                            <span class="spec-value">${drone.camara.zoom_optico || 'N/A'}x</span>
                        </div>
                        <div class="spec-row">
                            <span class="spec-label">Zoom Digital</span>
                            <span class="spec-value">${drone.camara.zoom_digital || 'N/A'}x</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="tab-content" id="features-tab">
            <div class="specs-grid">
                <div class="spec-group">
                    <h4><i class="fas fa-star"></i> Características de Vuelo</h4>
                    <div class="spec-list">
                        ${Object.entries(drone.features).map(([key, value]) => {
                            const featureNames = {
                                evita_obstaculos: 'Evitación de Obstáculos',
                                retorno_automatico: 'Retorno Automático',
                                seguimiento_objeto: 'Seguimiento de Objetos',
                                vuelo_nocturno: 'Vuelo Nocturno',
                                modo_sport: 'Modo Sport'
                            };
                            return `
                                <div class="spec-row">
                                    <span class="spec-label">${featureNames[key] || key}</span>
                                    <span class="spec-value">
                                        ${value ? '<i class="fas fa-check" style="color: var(--success-color)"></i>' : 
                                                '<i class="fas fa-times" style="color: var(--gray-400)"></i>'}
                                    </span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="tab-content" id="metrics-tab">
            <div class="specs-grid">
                <div class="spec-group">
                    <h4><i class="fas fa-chart-line"></i> Métricas de Rendimiento</h4>
                    <div class="spec-list">
                        <div class="spec-row">
                            <span class="spec-label">Score de Rendimiento</span>
                            <span class="spec-value">${Math.round(drone.metrics.performance_score || 0)}/100</span>
                        </div>
                        <div class="spec-row">
                            <span class="spec-label">Ratio Precio/Rendimiento</span>
                            <span class="spec-value">${(drone.metrics.price_performance_ratio || 0).toFixed(2)}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        ${drone.url ? `
            <div class="detail-actions mt-xl">
                <a href="${drone.url}" target="_blank" class="btn-primary">
                    <i class="fas fa-external-link-alt"></i>
                    Ver en sitio del fabricante
                </a>
            </div>
        ` : ''}
    `;
    
    modal.style.display = 'block';
};

window.showTab = function(tabName) {
    // Ocultar todos los tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Desactivar todos los botones
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Mostrar tab seleccionado
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Activar botón correspondiente
    event.target.classList.add('active');
};

// ========================================
// INSIGHTS
// ========================================

function loadInsights() {
    if (!window.droneData || !window.droneData.insights) return;
    
    const insightsList = document.getElementById('insights-list');
    insightsList.innerHTML = '';
    
    window.droneData.insights.forEach(insight => {
        const insightItem = document.createElement('div');
        insightItem.className = 'insight-item fade-in';
        insightItem.innerHTML = `
            <h5><i class="fas fa-lightbulb"></i> ${insight.tipo}</h5>
            <p>${insight.mensaje}</p>
        `;
        insightsList.appendChild(insightItem);
    });
}

// ========================================
// UTILIDADES
// ========================================

function formatPrice(price) {
    if (!price) return 'N/A';
    return `$${price.toLocaleString('es-ES')}`;
}

function formatDistance(meters) {
    if (!meters) return 'N/A';
    if (meters >= 1000) {
        return `${(meters / 1000).toFixed(1)} km`;
    }
    return `${meters} m`;
}

function updateResultsCount() {
    const count = appState.filteredDrones.length;
    document.getElementById('results-count').textContent = count;
}

function showLoading() {
    document.getElementById('loading-overlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

function showNotification(message, type = 'info') {
    // Implementación simple de notificaciones
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'warning' ? 'exclamation-triangle' : 
                           type === 'error' ? 'times-circle' : 
                           type === 'success' ? 'check-circle' : 
                           'info-circle'}"></i>
        ${message}
    `;
    
    document.body.appendChild(notification);
    
    // Estilos inline temporales
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '1rem 1.5rem',
        background: type === 'warning' ? '#f59e0b' :
                   type === 'error' ? '#ef4444' :
                   type === 'success' ? '#10b981' :
                   '#3b82f6',
        color: 'white',
        borderRadius: '0.5rem',
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
        zIndex: '9999',
        animation: 'slideIn 0.3s ease-out'
    });
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function showError(message) {
    showNotification(message, 'error');
}

// ========================================
// DATOS DE EJEMPLO (FALLBACK)
// ========================================

function generateSampleData() {
    // Generar datos de ejemplo si falla la carga
    return [
        {
            id: 1,
            modelo: "DJI Air 3",
            marca: "DJI",
            precio: 1099,
            imagen: "/assets/drone_icons/dji.png",
            specs: {
                peso: 720,
                autonomia: 46,
                alcance: 10000,
                velocidad: 68.4,
                resistencia_viento: "12 m/s",
                temperatura: "-10°C a 40°C"
            },
            camara: {
                resolucion: "4K",
                fps: 60,
                sensor: "1/1.3 inch CMOS",
                estabilizacion: "mecanica",
                zoom_optico: 3,
                zoom_digital: 9
            },
            features: {
                evita_obstaculos: true,
                retorno_automatico: true,
                seguimiento_objeto: true,
                vuelo_nocturno: false,
                modo_sport: true
            },
            clasificacion: {
                categoria: "medio",
                nivel: "avanzado",
                usos: ["fotografia", "video_profesional"]
            },
            metrics: {
                performance_score: 85,
                price_performance_ratio: 7.7
            }
        }
        // Agregar más drones de ejemplo según sea necesario
    ];
}

// Exportar estado para uso en otros módulos
window.appState = appState;