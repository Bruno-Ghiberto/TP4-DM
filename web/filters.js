// ========================================
// DRONE COMPARATOR - FILTERS MODULE
// ========================================

let appState = null;

export function initializeFilters(state) {
    appState = state;
    
    // Event listeners para filtros
    document.getElementById('apply-filters').addEventListener('click', applyFilters);
    document.getElementById('reset-filters').addEventListener('click', resetFilters);
    
    // Quick filters
    document.querySelectorAll('.quick-filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            applyQuickFilter(e.currentTarget.dataset.profile);
        });
    });
    
    // Auto-aplicar filtros en cambios
    initializeAutoApply();
}

export function applyFilters() {
    console.log('Aplicando filtros...');
    
    const filters = collectFilters();
    appState.filteredDrones = filterDrones(appState.allDrones, filters);
    appState.currentPage = 1;
    
    // Re-renderizar
    if (window.renderDrones) {
        window.renderDrones();
    }
    
    // Actualizar gráficos si están visibles
    if (appState.currentSection === 'insights' && window.updateCharts) {
        window.updateCharts(appState.filteredDrones);
    }
}

function collectFilters() {
    return {
        // Presupuesto
        maxBudget: parseInt(document.getElementById('budget-slider').value),
        
        // Marcas
        brands: Array.from(document.querySelectorAll('input[name="brand"]:checked'))
            .map(input => input.value),
        
        // Nivel de usuario
        userLevel: document.querySelector('input[name="user-level"]:checked').value,
        
        // Uso principal
        primaryUse: document.getElementById('primary-use').value,
        
        // Especificaciones mínimas
        minAutonomy: parseInt(document.getElementById('min-autonomy').value) || 0,
        minRange: parseInt(document.getElementById('min-range').value) || 0,
        maxWeight: parseInt(document.getElementById('max-weight').value) || Infinity,
        
        // Características requeridas
        requiredFeatures: Array.from(document.querySelectorAll('input[name="features"]:checked'))
            .map(input => input.value)
    };
}

function filterDrones(drones, filters) {
    return drones.filter(drone => {
        // Filtro de presupuesto
        if (drone.precio > filters.maxBudget) {
            return false;
        }
        
        // Filtro de marca
        if (filters.brands.length > 0 && !filters.brands.includes(drone.marca)) {
            return false;
        }
        
        // Filtro de nivel de usuario
        if (filters.userLevel !== 'all' && drone.clasificacion.nivel !== filters.userLevel) {
            return false;
        }
        
        // Filtro de uso principal
        if (filters.primaryUse !== 'all' && 
            !drone.clasificacion.usos.includes(filters.primaryUse)) {
            return false;
        }
        
        // Filtros de especificaciones
        if (drone.specs.autonomia < filters.minAutonomy) {
            return false;
        }
        
        if (drone.specs.alcance < filters.minRange) {
            return false;
        }
        
        if (drone.specs.peso > filters.maxWeight) {
            return false;
        }
        
        // Filtro de características requeridas
        for (const feature of filters.requiredFeatures) {
            if (!drone.features[feature]) {
                return false;
            }
        }
        
        return true;
    });
}

function resetFilters() {
    // Resetear todos los controles
    document.getElementById('budget-slider').value = 10000;
    document.getElementById('budget-value').textContent = '$10,000';
    
    document.querySelectorAll('input[name="brand"]').forEach(input => {
        input.checked = true;
    });
    
    document.querySelector('input[name="user-level"][value="all"]').checked = true;
    document.getElementById('primary-use').value = 'all';
    
    document.getElementById('min-autonomy').value = '';
    document.getElementById('min-range').value = '';
    document.getElementById('max-weight').value = '';
    
    document.querySelectorAll('input[name="features"]').forEach(input => {
        input.checked = false;
    });
    
    // Aplicar filtros reseteados
    applyFilters();
}

function applyQuickFilter(profile) {
    resetFilters();
    
    switch (profile) {
        case 'beginner':
            document.getElementById('budget-slider').value = 500;
            document.getElementById('budget-value').textContent = '$500';
            document.querySelector('input[name="user-level"][value="principiante"]').checked = true;
            document.querySelector('input[name="features"][value="retorno_automatico"]').checked = true;
            break;
            
        case 'photographer':
            document.getElementById('budget-slider').value = 2000;
            document.getElementById('budget-value').textContent = '$2,000';
            document.getElementById('primary-use').value = 'fotografia';
            document.querySelector('input[name="features"][value="evita_obstaculos"]').checked = true;
            document.getElementById('min-autonomy').value = 25;
            break;
            
        case 'professional':
            document.getElementById('budget-slider').value = 5000;
            document.getElementById('budget-value').textContent = '$5,000';
            document.querySelector('input[name="user-level"][value="profesional"]').checked = true;
            document.getElementById('primary-use').value = 'video_profesional';
            document.querySelector('input[name="features"][value="evita_obstaculos"]').checked = true;
            document.querySelector('input[name="features"][value="seguimiento_objeto"]').checked = true;
            break;
            
        case 'traveler':
            document.getElementById('max-weight').value = 700;
            document.getElementById('budget-slider').value = 1500;
            document.getElementById('budget-value').textContent = '$1,500';
            document.querySelector('input[name="features"][value="evita_obstaculos"]').checked = true;
            document.querySelector('input[name="features"][value="retorno_automatico"]').checked = true;
            break;
    }
    
    applyFilters();
}

function initializeAutoApply() {
    // Actualizar valor del slider de presupuesto
    const budgetSlider = document.getElementById('budget-slider');
    const budgetValue = document.getElementById('budget-value');
    
    budgetSlider.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        budgetValue.textContent = `${value.toLocaleString()}`;
    });
    
    // Auto-aplicar en cambios importantes
    const autoApplyElements = [
        'budget-slider',
        'primary-use'
    ];
    
    autoApplyElements.forEach(id => {
        document.getElementById(id).addEventListener('change', () => {
            setTimeout(applyFilters, 300);
        });
    });
}

// ========================================
// ANÁLISIS DE FILTROS
// ========================================

export function getFilterStats() {
    const filters = collectFilters();
    const filtered = filterDrones(appState.allDrones, filters);
    
    return {
        totalDrones: appState.allDrones.length,
        filteredDrones: filtered.length,
        filterPercentage: (filtered.length / appState.allDrones.length) * 100,
        activeFilters: countActiveFilters(filters)
    };
}

function countActiveFilters(filters) {
    let count = 0;
    
    if (filters.maxBudget < 10000) count++;
    if (filters.brands.length < 3) count++;
    if (filters.userLevel !== 'all') count++;
    if (filters.primaryUse !== 'all') count++;
    if (filters.minAutonomy > 0) count++;
    if (filters.minRange > 0) count++;
    if (filters.maxWeight < Infinity) count++;
    if (filters.requiredFeatures.length > 0) count += filters.requiredFeatures.length;
    
    return count;
}