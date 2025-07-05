// Global variables
let allDrones = [];
let filteredDrones = [];
let dronesPrices = {};
let currentFilters = {
    brand: 'all',
    category: 'all',
    search: ''
};

// Initialize the application
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await loadDroneData();
        await loadPricesData();
        
        // Check which drones don't have prices (commented for production)
        // console.log('=== Checking missing prices ===');
        // allDrones.forEach(drone => {
        //     const modelVariations = [
        //         drone.modelo,
        //         drone.modelo.trim(),
        //         drone.modelo.replace(/\s+/g, ' '),
        //         drone.modelo.replace('Evo', 'EVO'),
        //         drone.modelo.replace('EVO', 'Evo')
        //     ];
        //     
        //     let hasPrice = false;
        //     for (const variation of modelVariations) {
        //         if (dronesPrices[variation]) {
        //             hasPrice = true;
        //             break;
        //         }
        //     }
        //     
        //     if (!hasPrice) {
        //         console.log(`Missing price for: "${drone.modelo}"`);
        //     }
        // });
        // console.log('=== End price check ===');
        
        setupEventListeners();
        renderDroneGrid(allDrones);
        updateStatistics();
    } catch (error) {
        console.error('Error initializing app:', error);
        showError('Error al cargar los datos de drones');
    }
});

// Load prices data from CSV
async function loadPricesData() {
    try {
        const possiblePaths = [
            '../data/raw/prices.csv',
            'data/raw/prices.csv',
            '/data/raw/prices.csv'
        ];
        
        let response;
        for (const path of possiblePaths) {
            try {
                response = await fetch(path);
                if (response.ok) {
                    // console.log(`Successfully loaded prices from: ${path}`);
                    break;
                }
            } catch (e) {
                console.warn(`Failed to load prices from ${path}:`, e);
            }
        }
        
        if (response && response.ok) {
            const csvText = await response.text();
            const lines = csvText.trim().split('\n');
            
            // Skip header and process data
            for (let i = 1; i < lines.length; i++) {
                const [modelo, precio] = lines[i].split(',');
                if (modelo && precio) {
                    const cleanModel = modelo.trim();
                    const priceValue = parseInt(precio.trim());
                    
                    // Add the original model name
                    dronesPrices[cleanModel] = priceValue;
                    
                    // Create specific mappings for each drone model
                    switch(cleanModel) {
                        // DJI Models
                        case 'Mavic 3 Pro':
                            dronesPrices['Mavic 3 Pro'] = priceValue;
                            break;
                        case 'Mavic 3 Classic':
                            dronesPrices['Mavic 3 Classic'] = priceValue;
                            break;
                        case 'Air 3S':
                            dronesPrices['Air 3S'] = priceValue;
                            break;
                        case 'Air 3':
                            dronesPrices['Air 3'] = priceValue;
                            break;
                        case 'Mini 4 Pro':
                            dronesPrices['Mini 4 Pro'] = priceValue;
                            break;
                        case 'Mini 3':
                            dronesPrices['Mini 3'] = priceValue;
                            break;
                        case 'Avata 2':
                            dronesPrices['Avata 2'] = priceValue;
                            break;
                        case 'Inspire 3':
                            dronesPrices['Inspire 3'] = priceValue;
                            break;
                            
                        // Autel Models
                        case 'EVO Lite Enterprise (versión 6K)':
                            dronesPrices['Evo Lite Enterprise Series'] = priceValue;
                            dronesPrices['EVO Lite Enterprise Series'] = priceValue;
                            break;
                        case 'Autel Alpha (L35T)':
                            dronesPrices['Alpha'] = priceValue;
                            dronesPrices['Autel Alpha'] = priceValue;
                            break;
                        case 'EVO Max 4T':
                            dronesPrices['Evo Max 4T'] = priceValue;
                            dronesPrices['EVO Max 4T'] = priceValue;
                            break;
                        case 'EVO II Pro Enterprise V3':
                            dronesPrices['Evo II Enterprise V3'] = priceValue;
                            dronesPrices['EVO II Enterprise V3'] = priceValue;
                            break;
                        case 'EVO II Dual 640T V3':
                            dronesPrices['Evo II Dual 640T V3'] = priceValue;
                            dronesPrices['EVO II Dual 640T V3'] = priceValue;
                            break;
                        case 'EVO II Pro V3':
                            dronesPrices['Evo II Pro V3'] = priceValue;
                            dronesPrices['EVO II Pro V3'] = priceValue;
                            break;
                        case 'EVO II PRO':
                            dronesPrices['Evo II Pro'] = priceValue;
                            dronesPrices['EVO II PRO'] = priceValue;
                            dronesPrices['Evo II Pro V3'] = priceValue;
                            dronesPrices['EVO II Pro V3'] = priceValue;
                            break;
                        case 'Dragonfish (serie VTOL)':
                            dronesPrices['Dragonfish Series'] = priceValue;
                            dronesPrices['Dragonfish'] = priceValue;
                            break;
                            
                        // Parrot Models
                        case 'ANAFI Ai':
                            dronesPrices['Parrot Anafi AI'] = priceValue;
                            dronesPrices['Parrot ANAFI AI'] = priceValue;
                            dronesPrices['Anafi AI'] = priceValue;
                            break;
                        case 'ANAFI USA':
                            dronesPrices['Parrot Anafi USA'] = priceValue;
                            dronesPrices['Parrot ANAFI USA'] = priceValue;
                            dronesPrices['Anafi USA'] = priceValue;
                            break;
                    }
                    
                    // Additional mappings for EVO models
                    if (cleanModel.includes('EVO')) {
                        dronesPrices[cleanModel.replace('EVO', 'Evo')] = priceValue;
                    }
                }
            }
            
            // console.log('Loaded prices:', dronesPrices);
        }
    } catch (error) {
        console.error('Error loading prices:', error);
    }
}

// Load drone data from JSON file - UPDATED to use new file
async function loadDroneData() {
    try {
        let response;
        const possiblePaths = [
            '../data/processed/drones_web_ready.json',
            '../data/processed/drones_normalized.json',
            'data/processed/drones_normalized.json',
            '/data/processed/drones_normalized.json'
        ];
        
        for (const path of possiblePaths) {
            try {
                response = await fetch(path);
                if (response.ok) {
                    // console.log(`Successfully loaded data from: ${path}`);
                    break;
                }
            } catch (e) {
                console.warn(`Failed to load from ${path}:`, e);
            }
        }
        
        if (!response || !response.ok) {
            throw new Error('No se pudo cargar el archivo de datos');
        }
        
        allDrones = await response.json();
        filteredDrones = [...allDrones];
        
        // Create category dropdowns
        populateFilters();
        
        // console.log(`Loaded ${allDrones.length} drones`);
    } catch (error) {
        console.error('Error loading drone data:', error);
        throw error;
    }
}

// Setup event listeners
function setupEventListeners() {
    // Filter listeners
    document.getElementById('brandFilter').addEventListener('change', applyFilters);
    document.getElementById('categoryFilter').addEventListener('change', applyFilters);
    document.getElementById('searchInput').addEventListener('input', debounce(applyFilters, 300));
    
    // Sort listener
    document.getElementById('sortSelect').addEventListener('change', sortDrones);
    
    // Modal close listeners
    const modal = document.getElementById('droneModal');
    const closeBtn = document.querySelector('.close');
    
    closeBtn.onclick = () => modal.style.display = 'none';
    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };
}

// Apply filters
function applyFilters() {
    currentFilters.brand = document.getElementById('brandFilter').value;
    currentFilters.category = document.getElementById('categoryFilter').value;
    currentFilters.search = document.getElementById('searchInput').value.toLowerCase();
    
    filteredDrones = allDrones.filter(drone => {
        const brandMatch = currentFilters.brand === 'all' || drone.marca === currentFilters.brand;
        const categoryMatch = currentFilters.category === 'all' || drone.categoria === currentFilters.category;
        const searchMatch = currentFilters.search === '' || 
            drone.modelo.toLowerCase().includes(currentFilters.search) ||
            drone.marca.toLowerCase().includes(currentFilters.search) ||
            (drone.categoria && drone.categoria.toLowerCase().includes(currentFilters.search));
        
        return brandMatch && categoryMatch && searchMatch;
    });
    
    renderDroneGrid(filteredDrones);
    updateStatistics();
}

// Sort drones
function sortDrones() {
    const sortBy = document.getElementById('sortSelect').value;
    
    filteredDrones.sort((a, b) => {
        const specsA = a.especificaciones_tecnicas || {};
        const specsB = b.especificaciones_tecnicas || {};
        
        switch (sortBy) {
            case 'name':
                return a.modelo.localeCompare(b.modelo);
            case 'weight':
                return (specsA.peso_gramos || 0) - (specsB.peso_gramos || 0);
            case 'flightTime':
                return (specsB.vuelo_minutos || 0) - (specsA.vuelo_minutos || 0);
            case 'range':
                return (specsB.alcance_video_km || 0) - (specsA.alcance_video_km || 0);
            case 'score':
                return (b.puntuacion_general || 0) - (a.puntuacion_general || 0);
            default:
                return 0;
        }
    });
    
    renderDroneGrid(filteredDrones);
}

// Render drone grid
function renderDroneGrid(drones) {
    const grid = document.getElementById('droneGrid');
    
    if (drones.length === 0) {
        grid.innerHTML = '<div class="no-results">No se encontraron drones con los filtros seleccionados</div>';
        return;
    }
    
    grid.innerHTML = drones.map(drone => createDroneCard(drone)).join('');
}

// Map model names to image filenames
function getImageFileName(modelo) {
    // Create a mapping for specific cases
    const imageMapping = {
        // Parrot drones
        'Parrot Anafi AI': 'ANAFI-AI',
        'Parrot Anafi USA': 'Anafi-USA',
        
        // Autel drones
        'Evo Lite Enterprise Series': 'EVO Lite Enterprise',
        'Evo Max 4T': 'EVO-Max-4T',
        'Evo II Enterprise V3': 'EVO II Enterprise',
        'Evo II Dual 640T V3': 'EVO II Dual 640t',
        'Evo II Pro V3': 'EVO II PRO',
        'Dragonfish Series': 'Dragonfish',
        'Alpha': 'Alpha',
        
        // DJI drones
        'Mavic 3 Pro': 'Mavic 3 Pro',
        'Mavic 3 Classic': 'Mavic 3 Classic',
        'Air 3S': 'Air 3S',
        'Air 3': 'Air 3',
        'Mini 4 Pro': 'Mini 4 Pro',
        'Mini 3': 'Mini 3',
        'Avata 2': 'Avata 2',
        'Inspire 3': 'Inspire 3'
    };
    
    // Check if we have a specific mapping
    if (imageMapping[modelo]) {
        return imageMapping[modelo];
    }
    
    // Otherwise return the model name as is
    return modelo;
}

// Create drone card HTML - UPDATED for new data structure
function createDroneCard(drone) {
    const specs = drone.especificaciones_tecnicas || {};
    
    // Use brand logo for card preview
    const logoUrl = getDefaultImage(drone.marca);
    
    // Get price - try multiple variations
    let price = null;
    const modelVariations = [
        drone.modelo,
        drone.modelo.trim(),
        drone.modelo.replace(/\s+/g, ' '),
        drone.modelo.replace('Evo', 'EVO'),
        drone.modelo.replace('EVO', 'Evo')
    ];
    
    for (const variation of modelVariations) {
        if (dronesPrices[variation]) {
            price = dronesPrices[variation];
            break;
        }
    }
    
    // Debug log if no price found (commented for production)
    // if (!price) {
    //     console.log(`No price found for: "${drone.modelo}"`);
    // }
    
    const priceDisplay = price ? `$${price.toLocaleString()} USD` : 'Precio no disponible';
    
    // Create features HTML
    const featuresHtml = (specs.caracteristicas_destacadas || [])
        .slice(0, 3)  // Show max 3 features
        .map(feature => `<span class="feature-tag">${feature}</span>`)
        .join('');
    
    // Format specifications
    const weight = specs.peso_gramos ? `${specs.peso_gramos}g` : 'N/A';
    const flightTime = specs.vuelo_minutos ? `${specs.vuelo_minutos} min` : 'N/A';
    const range = specs.alcance_video_km ? `${specs.alcance_video_km} km` : 'N/A';
    const camera = formatCameraSpec(specs.sensor_camara);
    const video = formatVideoSpec(specs.resolucion_video);
    const obstacle = specs.deteccion_obstaculos ? 'Sí' : 'No';
    
    // Score styling
    const score = drone.puntuacion_general || 0;
    const scoreClass = score >= 8 ? 'high' : score >= 6 ? 'medium' : 'low';
    
    return `
        <div class="drone-card" data-drone-id="${drone.modelo}">
            <div class="card-header">
                <img src="${logoUrl}" alt="${drone.marca}" class="drone-image brand-logo">
                <div class="card-badges">
                    <span class="brand-badge">${drone.marca}</span>
                    <span class="category-badge">${drone.categoria || 'General'}</span>
                </div>
                <div class="score-badge ${scoreClass}">
                    ${score.toFixed(1)}
                </div>
            </div>
            
            <div class="card-body">
                <h3 class="drone-name">${drone.modelo}</h3>
                <div class="drone-price">${priceDisplay}</div>
                
                ${featuresHtml ? `<div class="features-container">${featuresHtml}</div>` : ''}
                
                <div class="specs-grid">
                    <div class="spec-item">
                        <i class="fas fa-weight"></i>
                        <span class="spec-label">Peso</span>
                        <span class="spec-value">${weight}</span>
                    </div>
                    <div class="spec-item">
                        <i class="fas fa-clock"></i>
                        <span class="spec-label">Vuelo</span>
                        <span class="spec-value">${flightTime}</span>
                    </div>
                    <div class="spec-item">
                        <i class="fas fa-wifi"></i>
                        <span class="spec-label">Alcance</span>
                        <span class="spec-value">${range}</span>
                    </div>
                    <div class="spec-item">
                        <i class="fas fa-camera"></i>
                        <span class="spec-label">Cámara</span>
                        <span class="spec-value" title="${specs.sensor_camara || 'N/A'}">${camera}</span>
                    </div>
                    <div class="spec-item">
                        <i class="fas fa-video"></i>
                        <span class="spec-label">Video</span>
                        <span class="spec-value">${video}</span>
                    </div>
                    <div class="spec-item">
                        <i class="fas fa-shield-alt"></i>
                        <span class="spec-label">Obstáculos</span>
                        <span class="spec-value">${obstacle}</span>
                    </div>
                </div>
                
                <div class="card-footer">
                    <button class="btn-details" onclick="showDroneDetails('${encodeURIComponent(drone.modelo)}')">
                        Ver detalles
                    </button>
                    <a href="${drone.url_fuente}" target="_blank" class="btn-source">
                        <i class="fas fa-external-link-alt"></i> Fuente
                    </a>
                </div>
            </div>
        </div>
    `;
}

// Format camera specification for display
function formatCameraSpec(camera) {
    if (!camera || camera === 'No especificado') return 'N/A';
    if (camera.length > 20) return camera.substring(0, 20) + '...';
    return camera;
}

// Format video specification for display
function formatVideoSpec(video) {
    if (!video || video === 'No especificado' || video === '') return 'N/A';
    return video;
}

// Get default image based on brand
function getDefaultImage(brand) {
    const brandLower = (brand || '').toLowerCase();
    return `../data/images/${brandLower}-logo.png`;
}

// Populate filter dropdowns - UPDATED
function populateFilters() {
    // Get unique brands and categories
    const brands = [...new Set(allDrones.map(d => d.marca))].sort();
    const categories = [...new Set(allDrones.map(d => d.categoria))].filter(Boolean).sort();
    
    // Populate brand filter
    const brandSelect = document.getElementById('brandFilter');
    if (brandSelect) {
        brandSelect.innerHTML = '<option value="all">Todas las marcas</option>';
        brands.forEach(brand => {
            brandSelect.innerHTML += `<option value="${brand}">${brand}</option>`;
        });
    }
    
    // Populate category filter
    const categorySelect = document.getElementById('categoryFilter');
    if (categorySelect) {
        categorySelect.innerHTML = '<option value="all">Todas las categorías</option>';
        categories.forEach(category => {
            categorySelect.innerHTML += `<option value="${category}">${category}</option>`;
        });
    }
}

// Show drone details modal - UPDATED
function showDroneDetails(encodedModel) {
    const droneModel = decodeURIComponent(encodedModel);
    const drone = allDrones.find(d => d.modelo === droneModel);
    if (!drone) return;
    
    const modal = document.getElementById('droneModal');
    const specs = drone.especificaciones_tecnicas || {};
    
    // Get price - try multiple variations
    let price = null;
    const modelVariations = [
        drone.modelo,
        drone.modelo.trim(),
        drone.modelo.replace(/\s+/g, ' '),
        drone.modelo.replace('Evo', 'EVO'),
        drone.modelo.replace('EVO', 'Evo')
    ];
    
    for (const variation of modelVariations) {
        if (dronesPrices[variation]) {
            price = dronesPrices[variation];
            break;
        }
    }
    
    const priceDisplay = price ? `$${price.toLocaleString()} USD` : '';
    
    // Get image URL
    let imageUrl = drone.imagen;
    if (imageUrl && !imageUrl.includes('-logo.png')) {
        // Fix the path if it starts with 'data/images/'
        if (imageUrl.startsWith('data/images/')) {
            imageUrl = '../' + imageUrl;
        }
    } else {
        // Fallback: try to build the image URL
        const imageName = getImageFileName(drone.modelo);
        imageUrl = `../data/images/${imageName}.jpg`;
    }
    
    // Build detailed specs HTML
    let specsHtml = '<div class="detailed-specs">';
    
    // Main specifications
    const mainSpecs = [
        { label: 'Peso', value: specs.peso_gramos ? `${specs.peso_gramos} gramos` : 'No especificado', icon: 'fa-weight' },
        { label: 'Dimensiones (plegado)', value: specs.dimensiones_plegado || 'No especificado', icon: 'fa-ruler' },
        { label: 'Tiempo de vuelo', value: specs.vuelo_minutos ? `${specs.vuelo_minutos} minutos` : 'No especificado', icon: 'fa-clock' },
        { label: 'Velocidad horizontal', value: specs.vel_horizontal_mps ? `${specs.vel_horizontal_mps} m/s` : 'No especificado', icon: 'fa-tachometer-alt' },
        { label: 'Velocidad ascenso', value: specs.vel_ascenso_mps ? `${specs.vel_ascenso_mps} m/s` : 'No especificado', icon: 'fa-arrow-up' },
        { label: 'Alcance video', value: specs.alcance_video_km ? `${specs.alcance_video_km} km` : 'No especificado', icon: 'fa-wifi' },
        { label: 'Altitud máxima', value: specs.altitud_despegue_m ? `${specs.altitud_despegue_m} m` : 'No especificado', icon: 'fa-mountain' },
        { label: 'Resistencia al viento', value: specs.resistencia_viento_mps ? `${specs.resistencia_viento_mps} m/s` : 'No especificado', icon: 'fa-wind' },
        { label: 'Almacenamiento', value: specs.almacenamiento_interno_gb ? `${specs.almacenamiento_interno_gb} GB` : 'No especificado', icon: 'fa-hdd' },
        { label: 'Sensor cámara', value: specs.sensor_camara || 'No especificado', icon: 'fa-camera' },
        { label: 'Resolución video', value: specs.resolucion_video || 'No especificado', icon: 'fa-video' },
        { label: 'Detección obstáculos', value: specs.deteccion_obstaculos ? 'Sí' : 'No', icon: 'fa-shield-alt' }
    ];
    
    mainSpecs.forEach(spec => {
        specsHtml += `
            <div class="spec-row">
                <i class="fas ${spec.icon}"></i>
                <span class="spec-label">${spec.label}:</span>
                <span class="spec-value">${spec.value}</span>
            </div>
        `;
    });
    
    specsHtml += '</div>';
    
    // Features
    if (specs.caracteristicas_destacadas && specs.caracteristicas_destacadas.length > 0) {
        specsHtml += '<div class="features-section"><h4>Características destacadas</h4><div class="features-list">';
        specs.caracteristicas_destacadas.forEach(feature => {
            specsHtml += `<span class="feature-highlight">${feature}</span>`;
        });
        specsHtml += '</div></div>';
    }
    
    // Update modal content
    document.getElementById('modalDroneName').textContent = drone.modelo;
    document.getElementById('modalDroneBrand').textContent = drone.marca;
    document.getElementById('modalDroneCategory').textContent = drone.categoria || 'General';
    document.getElementById('modalDroneSpecs').innerHTML = specsHtml;
    
    // Update image with better error handling
    const modalImage = document.getElementById('modalDroneImage');
    
    modalImage.src = imageUrl;
    modalImage.alt = drone.modelo;
    
    // Handle image loading errors
    modalImage.onerror = function() {
        // Try with different extension (.jpeg instead of .jpg or vice versa)
        if (this.src.endsWith('.jpg')) {
            const jpegUrl = this.src.replace('.jpg', '.jpeg');
            this.src = jpegUrl;
            this.onerror = function() {
                // If still fails, use brand logo
                this.onerror = null;
                this.src = getDefaultImage(drone.marca);
            };
        } else if (this.src.endsWith('.jpeg')) {
            const jpgUrl = this.src.replace('.jpeg', '.jpg');
            this.src = jpgUrl;
            this.onerror = function() {
                // If still fails, use brand logo
                this.onerror = null;
                this.src = getDefaultImage(drone.marca);
            };
        } else {
            // Use brand logo as fallback
            this.onerror = null;
            this.src = getDefaultImage(drone.marca);
        }
    };
    
    // Add price to modal
    const modalInfo = document.querySelector('.modal-info');
    const existingPrice = modalInfo.querySelector('.modal-price');
    if (existingPrice) {
        existingPrice.remove();
    }
    
    if (priceDisplay) {
        const priceElement = document.createElement('div');
        priceElement.className = 'modal-price';
        priceElement.textContent = priceDisplay;
        modalInfo.insertBefore(priceElement, modalInfo.querySelector('.modal-badges'));
    }
    
    document.getElementById('modalDroneScore').textContent = `Puntuación: ${(drone.puntuacion_general || 0).toFixed(1)}/10`;
    document.getElementById('modalDroneScore').className = `modal-score ${getScoreClass(drone.puntuacion_general)}`;
    document.getElementById('modalSourceLink').href = drone.url_fuente;
    
    // Show modal
    modal.style.display = 'block';
}

// Get score class
function getScoreClass(score) {
    if (score >= 8) return 'high';
    if (score >= 6) return 'medium';
    return 'low';
}

// Update statistics - UPDATED
function updateStatistics() {
    // Count by brand
    const brandCounts = {};
    const categoryCounts = {};
    
    filteredDrones.forEach(drone => {
        brandCounts[drone.marca] = (brandCounts[drone.marca] || 0) + 1;
        if (drone.categoria) {
            categoryCounts[drone.categoria] = (categoryCounts[drone.categoria] || 0) + 1;
        }
    });
    
    // Update UI only if elements exist
    const totalDronesEl = document.getElementById('totalDrones');
    if (totalDronesEl) {
        totalDronesEl.textContent = filteredDrones.length;
    }
    
    const totalBrandsEl = document.getElementById('totalBrands');
    if (totalBrandsEl) {
        totalBrandsEl.textContent = Object.keys(brandCounts).length;
    }
    
    const totalCategoriesEl = document.getElementById('totalCategories');
    if (totalCategoriesEl) {
        totalCategoriesEl.textContent = Object.keys(categoryCounts).length;
    }
    
    // Calculate average score
    const avgScore = filteredDrones.length > 0 
        ? filteredDrones.reduce((sum, d) => sum + (d.puntuacion_general || 0), 0) / filteredDrones.length 
        : 0;
    
    const avgScoreElement = document.getElementById('avgScore');
    if (avgScoreElement) {
        avgScoreElement.textContent = avgScore.toFixed(1);
    }
}

// Show error message
function showError(message) {
    const grid = document.getElementById('droneGrid');
    grid.innerHTML = `<div class="error-message">${message}</div>`;
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Recommendation System Variables
let currentQuizStep = 0;
let userPreferences = {};

// Quiz Questions
const quizQuestions = [
    {
        id: 'usage',
        question: '¿Para qué usarás principalmente el drone?',
        options: [
            { value: 'photography', label: 'Fotografía y Video', icon: '📸' },
            { value: 'professional', label: 'Uso Profesional', icon: '💼' },
            { value: 'recreation', label: 'Recreación y Diversión', icon: '🎮' },
            { value: 'racing', label: 'Carreras FPV', icon: '🏁' }
        ]
    },
    {
        id: 'experience',
        question: '¿Cuál es tu nivel de experiencia?',
        options: [
            { value: 'beginner', label: 'Principiante', icon: '🌱' },
            { value: 'intermediate', label: 'Intermedio', icon: '📈' },
            { value: 'advanced', label: 'Avanzado', icon: '🚀' }
        ]
    },
    {
        id: 'budget',
        question: '¿Cuál es tu presupuesto aproximado?',
        options: [
            { value: 'low', label: 'Menos de $500', icon: '💵' },
            { value: 'medium', label: '$500 - $1500', icon: '💰' },
            { value: 'high', label: '$1500 - $3000', icon: '💎' },
            { value: 'premium', label: 'Más de $3000', icon: '👑' }
        ]
    },
    {
        id: 'portability',
        question: '¿Qué tan importante es la portabilidad?',
        options: [
            { value: 'very', label: 'Muy importante', icon: '🎒' },
            { value: 'moderate', label: 'Moderadamente', icon: '📦' },
            { value: 'not', label: 'No es importante', icon: '🏠' }
        ]
    },
    {
        id: 'features',
        question: '¿Qué característica es más importante para ti?',
        options: [
            { value: 'camera', label: 'Calidad de cámara', icon: '📷' },
            { value: 'flight-time', label: 'Tiempo de vuelo', icon: '⏱️' },
            { value: 'range', label: 'Alcance', icon: '📡' },
            { value: 'obstacle', label: 'Evitación de obstáculos', icon: '🛡️' }
        ]
    }
];

// Start recommendation quiz
function startRecommendation() {
    currentQuizStep = 0;
    userPreferences = {};
    
    const quizContainer = document.getElementById('recommendationQuiz');
    const resultsContainer = document.getElementById('recommendationResults');
    const startButton = document.querySelector('.recommendation-btn');
    
    startButton.style.display = 'none';
    quizContainer.style.display = 'block';
    resultsContainer.style.display = 'none';
    
    showQuizQuestion();
}

// Show current quiz question
function showQuizQuestion() {
    const quizContainer = document.getElementById('recommendationQuiz');
    const question = quizQuestions[currentQuizStep];
    
    let html = `
        <div class="quiz-question">
            <h3>${question.question}</h3>
            <div class="quiz-progress">
                <div class="progress-bar" style="width: ${((currentQuizStep + 1) / quizQuestions.length) * 100}%"></div>
            </div>
            <div class="quiz-options">
    `;
    
    question.options.forEach(option => {
        html += `
            <div class="quiz-option" onclick="selectOption('${question.id}', '${option.value}', this)">
                <span style="font-size: 2rem; display: block; margin-bottom: 0.5rem;">${option.icon}</span>
                <span>${option.label}</span>
            </div>
        `;
    });
    
    html += `
            </div>
            <div class="quiz-navigation">
                <button class="quiz-btn" onclick="previousQuestion()" ${currentQuizStep === 0 ? 'disabled' : ''}>
                    <i class="fas fa-arrow-left"></i> Anterior
                </button>
                <button class="quiz-btn" onclick="nextQuestion()" id="nextBtn" disabled>
                    ${currentQuizStep === quizQuestions.length - 1 ? 'Ver Resultados' : 'Siguiente'} <i class="fas fa-arrow-right"></i>
                </button>
            </div>
        </div>
    `;
    
    quizContainer.innerHTML = html;
    
    // Add progress bar styles
    const style = document.createElement('style');
    style.textContent = `
        .quiz-progress {
            width: 100%;
            height: 8px;
            background: var(--dark-border);
            border-radius: 4px;
            margin: 1rem 0 2rem;
            overflow: hidden;
        }
        .progress-bar {
            height: 100%;
            background: var(--accent-gradient);
            transition: width 0.3s ease;
        }
    `;
    if (!document.querySelector('style[data-quiz-progress]')) {
        style.setAttribute('data-quiz-progress', 'true');
        document.head.appendChild(style);
    }
}

// Select quiz option
function selectOption(questionId, value, element) {
    // Remove previous selection
    element.parentNode.querySelectorAll('.quiz-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    
    // Add selection
    element.classList.add('selected');
    
    // Store preference
    userPreferences[questionId] = value;
    
    // Enable next button
    document.getElementById('nextBtn').disabled = false;
}

// Previous question
function previousQuestion() {
    if (currentQuizStep > 0) {
        currentQuizStep--;
        showQuizQuestion();
    }
}

// Next question
function nextQuestion() {
    if (currentQuizStep < quizQuestions.length - 1) {
        currentQuizStep++;
        showQuizQuestion();
    } else {
        showRecommendations();
    }
}

// Calculate drone score based on preferences
function calculateDroneScore(drone, preferences) {
    let score = 0;
    let matchReasons = [];
    
    const specs = drone.especificaciones_tecnicas || {};
    
    // Budget matching
    const price = getDronePrice(drone.modelo);
    if (price) {
        switch (preferences.budget) {
            case 'low':
                if (price < 500) {
                    score += 25;
                    matchReasons.push('Precio accesible');
                }
                break;
            case 'medium':
                if (price >= 500 && price <= 1500) {
                    score += 25;
                    matchReasons.push('Precio en tu rango');
                }
                break;
            case 'high':
                if (price > 1500 && price <= 3000) {
                    score += 25;
                    matchReasons.push('Precio premium');
                }
                break;
            case 'premium':
                if (price > 3000) {
                    score += 25;
                    matchReasons.push('Máxima gama');
                }
                break;
        }
    }
    
    // Usage matching
    switch (preferences.usage) {
        case 'photography':
            if (specs.sensor_camara && specs.sensor_camara !== 'No especificado') {
                score += 20;
                if (specs.resolucion_video && specs.resolucion_video.includes('4K')) {
                    score += 10;
                    matchReasons.push('Excelente para fotografía');
                }
            }
            break;
        case 'professional':
            if (drone.categoria === 'Profesional' || drone.categoria === 'Enterprise') {
                score += 30;
                matchReasons.push('Diseñado para profesionales');
            }
            break;
        case 'recreation':
            if (drone.categoria === 'Consumer' || drone.categoria === 'Prosumer') {
                score += 20;
                matchReasons.push('Ideal para recreación');
            }
            break;
        case 'racing':
            if (drone.modelo.toLowerCase().includes('fpv') || drone.modelo.toLowerCase().includes('avata')) {
                score += 30;
                matchReasons.push('Perfecto para FPV');
            }
            break;
    }
    
    // Experience level matching
    switch (preferences.experience) {
        case 'beginner':
            if (specs.deteccion_obstaculos) {
                score += 15;
                matchReasons.push('Sistema anti-colisión');
            }
            if (drone.modelo.toLowerCase().includes('mini')) {
                score += 10;
                matchReasons.push('Fácil de manejar');
            }
            break;
        case 'advanced':
            if (drone.categoria === 'Profesional' || specs.caracteristicas_destacadas?.length > 5) {
                score += 15;
                matchReasons.push('Funciones avanzadas');
            }
            break;
    }
    
    // Portability matching
    if (preferences.portability === 'very' && specs.peso_gramos) {
        if (specs.peso_gramos < 500) {
            score += 20;
            matchReasons.push('Ultra portable');
        } else if (specs.peso_gramos < 1000) {
            score += 10;
            matchReasons.push('Portable');
        }
    }
    
    // Feature preferences
    switch (preferences.features) {
        case 'camera':
            if (specs.sensor_camara && specs.sensor_camara !== 'No especificado') {
                score += 15;
            }
            break;
        case 'flight-time':
            if (specs.vuelo_minutos && specs.vuelo_minutos > 25) {
                score += 15;
                matchReasons.push('Largo tiempo de vuelo');
            }
            break;
        case 'range':
            if (specs.alcance_video_km && specs.alcance_video_km > 5) {
                score += 15;
                matchReasons.push('Gran alcance');
            }
            break;
        case 'obstacle':
            if (specs.deteccion_obstaculos) {
                score += 15;
                matchReasons.push('Evitación de obstáculos');
            }
            break;
    }
    
    return { score, matchReasons };
}

// Get drone price helper
function getDronePrice(modelo) {
    const modelVariations = [
        modelo,
        modelo.trim(),
        modelo.replace(/\s+/g, ' '),
        modelo.replace('Evo', 'EVO'),
        modelo.replace('EVO', 'Evo')
    ];
    
    for (const variation of modelVariations) {
        if (dronesPrices[variation]) {
            return dronesPrices[variation];
        }
    }
    return null;
}

// Show recommendations
function showRecommendations() {
    const quizContainer = document.getElementById('recommendationQuiz');
    const resultsContainer = document.getElementById('recommendationResults');
    
    quizContainer.style.display = 'none';
    resultsContainer.style.display = 'block';
    
    // Calculate scores for all drones
    const scoredDrones = allDrones.map(drone => {
        const { score, matchReasons } = calculateDroneScore(drone, userPreferences);
        return { ...drone, matchScore: score, matchReasons };
    });
    
    // Sort by score and get top 3
    const recommendations = scoredDrones
        .sort((a, b) => b.matchScore - a.matchScore)
        .slice(0, 3);
    
    // Generate HTML for recommendations
    let html = `
        <h2 class="results-title">
            <i class="fas fa-star"></i> Tus Drones Recomendados
        </h2>
        <div class="recommended-drones">
    `;
    
    recommendations.forEach((drone, index) => {
        const price = getDronePrice(drone.modelo);
        const priceDisplay = price ? `$${price.toLocaleString()} USD` : 'Precio no disponible';
        
        html += `
            <div class="drone-card" style="position: relative;">
                <div class="match-percentage">${drone.matchScore}% Compatible</div>
                ${createDroneCardContent(drone, priceDisplay)}
                <div style="padding: 0 2rem 1rem;">
                    <h4 style="color: var(--primary-color); margin-bottom: 0.5rem;">¿Por qué este drone?</h4>
                    <ul style="list-style: none; padding: 0;">
                        ${drone.matchReasons.map(reason => `<li style="margin-bottom: 0.25rem;">✓ ${reason}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    });
    
    html += `
        </div>
        <div style="text-align: center; margin-top: 2rem;">
            <button class="recommendation-btn" onclick="resetRecommendation()">
                <i class="fas fa-redo"></i> Hacer otra búsqueda
            </button>
        </div>
    `;
    
    resultsContainer.innerHTML = html;
}

// Create drone card content (helper function)
function createDroneCardContent(drone, priceDisplay) {
    const specs = drone.especificaciones_tecnicas || {};
    const logoUrl = getDefaultImage(drone.marca);
    const score = drone.puntuacion_general || 0;
    const scoreClass = score >= 8 ? 'high' : score >= 6 ? 'medium' : 'low';
    
    const weight = specs.peso_gramos ? `${specs.peso_gramos}g` : 'N/A';
    const flightTime = specs.vuelo_minutos ? `${specs.vuelo_minutos} min` : 'N/A';
    const range = specs.alcance_video_km ? `${specs.alcance_video_km} km` : 'N/A';
    const camera = formatCameraSpec(specs.sensor_camara);
    const video = formatVideoSpec(specs.resolucion_video);
    const obstacle = specs.deteccion_obstaculos ? 'Sí' : 'No';
    
    return `
        <div class="card-header">
            <img src="${logoUrl}" alt="${drone.marca}" class="drone-image brand-logo">
            <div class="card-badges">
                <span class="brand-badge">${drone.marca}</span>
                <span class="category-badge">${drone.categoria || 'General'}</span>
            </div>
            <div class="score-badge ${scoreClass}">
                ${score.toFixed(1)}
            </div>
        </div>
        
        <div class="card-body">
            <h3 class="drone-name">${drone.modelo}</h3>
            <div class="drone-price">${priceDisplay}</div>
            
            <div class="specs-grid">
                <div class="spec-item">
                    <i class="fas fa-weight"></i>
                    <span class="spec-label">Peso</span>
                    <span class="spec-value">${weight}</span>
                </div>
                <div class="spec-item">
                    <i class="fas fa-clock"></i>
                    <span class="spec-label">Vuelo</span>
                    <span class="spec-value">${flightTime}</span>
                </div>
                <div class="spec-item">
                    <i class="fas fa-wifi"></i>
                    <span class="spec-label">Alcance</span>
                    <span class="spec-value">${range}</span>
                </div>
                <div class="spec-item">
                    <i class="fas fa-camera"></i>
                    <span class="spec-label">Cámara</span>
                    <span class="spec-value" title="${specs.sensor_camara || 'N/A'}">${camera}</span>
                </div>
            </div>
        </div>
    `;
}

// Reset recommendation system
function resetRecommendation() {
    const quizContainer = document.getElementById('recommendationQuiz');
    const resultsContainer = document.getElementById('recommendationResults');
    const startButton = document.querySelector('.recommendation-btn');
    
    quizContainer.style.display = 'none';
    resultsContainer.style.display = 'none';
    startButton.style.display = 'inline-flex';
    
    currentQuizStep = 0;
    userPreferences = {};
}

// Make showDroneDetails globally available
window.showDroneDetails = showDroneDetails;
