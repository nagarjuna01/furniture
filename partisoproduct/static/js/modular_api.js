// static/js/modular_api.js

// Base URL for the modular product and quoting API endpoints
const MODULAR_API_BASE = '/partiso/api'; 
// Base URL for the material API endpoints
const MATERIAL_API_BASE = '/material/v1';

// Function to get the CSRF token from a cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Function to perform a fetch request with CSRF header
async function performApiRequest(url, method, data = null) {
    const csrftoken = getCookie('csrftoken');
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        }
    };
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            const errorText = await response.text();
            let errorJson = {};
            try {
                errorJson = JSON.parse(errorText);
            } catch (e) {
                errorJson = { detail: errorText };
            }
            throw { status: response.status, message: response.statusText, details: errorJson };
        }
        if (response.status !== 204) { // 204 No Content for successful DELETE
            return await response.json();
        }
        return null; // For successful DELETE
    } catch (error) {
        console.error(`API Error (${method} ${url}):`, error);
        throw error; // Re-throw the error for the caller to handle
    }
}

/**
 * Generic function to fetch all items from a given API endpoint under MODULAR_API_BASE.
 * @param {string} endpoint - The API endpoint (e.g., 'modular1', 'parts', 'quote-requests').
 * @returns {Promise<Array>} A promise that resolves to an array of items.
 */
export async function fetchAll(endpoint) {
    const url = `${MODULAR_API_BASE}/${endpoint}/`;
    return performApiRequest(url, 'GET');
}

/**
 * Generic function to fetch a single item by ID from a given API endpoint under MODULAR_API_BASE.
 * @param {string} endpoint - The API endpoint.
 * @param {string|number} id - The ID of the item.
 * @returns {Promise<Object>} A promise that resolves to the item object.
 */
export async function fetchItem(endpoint, id) {
    const url = `${MODULAR_API_BASE}/${endpoint}/${id}/`;
    return performApiRequest(url, 'GET');
}

/**
 * Generic function to create an item at a given API endpoint under MODULAR_API_BASE.
 * @param {string} endpoint - The API endpoint.
 * @param {Object} data - The data for the item to create.
 * @returns {Promise<Object>} A promise that resolves to the created item object.
 */
export async function createItem(endpoint, data) {
    const url = `${MODULAR_API_BASE}/${endpoint}/`;
    return performApiRequest(url, 'POST', data);
}

/**
 * Generic function to update an item by ID at a given API endpoint under MODULAR_API_BASE.
 * @param {string} endpoint - The API endpoint.
 * @param {string|number} id - The ID of the item to update.
 * @param {Object} data - The data to update the item with.
 * @returns {Promise<Object>} A promise that resolves to the updated item object.
 */
export async function updateItem(endpoint, id, data) {
    const url = `${MODULAR_API_BASE}/${endpoint}/${id}/`;
    return performApiRequest(url, 'PUT', data); // Use PUT for full update
}

/**
 * Generic function to partially update an item by ID at a given API endpoint under MODULAR_API_BASE.
 * @param {string} endpoint - The API endpoint.
 * @param {string|number} id - The ID of the item to partially update.
 * @param {Object} data - The data to partially update the item with.
 * @returns {Promise<Object>} A promise that resolves to the updated item object.
 */
export async function patchItem(endpoint, id, data) {
    const url = `${MODULAR_API_BASE}/${endpoint}/${id}/`;
    return performApiRequest(url, 'PATCH', data); // Use PATCH for partial update
}

/**
 * Generic function to delete an item by ID at a given API endpoint under MODULAR_API_BASE.
 * @param {string} endpoint - The API endpoint.
 * @param {string|number} id - The ID of the item to delete.
 * @returns {Promise<null>} A promise that resolves to null on successful deletion.
 */
export async function deleteItem(endpoint, id) {
    const url = `${MODULAR_API_BASE}/${endpoint}/${id}/`;
    return performApiRequest(url, 'DELETE');
}

// --- Modular Product CRUD ---
export async function fetchModularProducts() {
    return fetchAll('modular1'); // Aligned with viewsets: 'modular-products'
}

export async function fetchModularProductDetail(productId) {
    return fetchItem('modular1', productId);
}

export async function createModularProduct(productData) {
    return createItem('modular1', productData);
}

export async function updateModularProduct(productId, productData) {
    return updateItem('modular1', productId, productData);
}

export async function deleteModularProduct(productId) {
    return deleteItem('modular1', productId);
}

export async function validateModularProductDimensions(productId, dimensions) {
    const url = `${MODULAR_API_BASE}/modular1/${productId}/validate-product-dimensions/`;
    return performApiRequest(url, 'POST', dimensions);
}


// --- Part1 (Product Parts) CRUD ---
export async function fetchModularParts(modularProductId = null, partId = null) {
    if (!MODULAR_API_BASE) {
        console.error("MODULAR_API_BASE is undefined!");
        return;
    }

    if (partId) {
        console.log('fetchModularParts: Fetching single part with partId:', partId);
        return fetchItem('parts', partId);
    }

    let url = `${MODULAR_API_BASE}/parts/`;
    if (modularProductId) {
        url += `?modular_product=${modularProductId}`;
    }
    
        return performApiRequest(url, 'GET');
}

export async function createModularPart(partData) {
    return createItem('parts', partData);
}

export async function updateModularPart(partId, partData) {
    return updateItem('parts', partId, partData);
}

export async function deleteModularPart(partId) {
    return deleteItem('parts', partId);
}

// --- Constraint (Product Parameters) CRUD ---
export async function fetchModularParameters(modularProductId = null, parameterId = null) {
    if (parameterId) return fetchItem('constraints', parameterId);
    let url = `${MODULAR_API_BASE}/constraints/`;
    if (modularProductId) url += `?modular_product=${modularProductId}`;
    return performApiRequest(url, 'GET');
}


export async function createModularParameter(parameterData) {
    return createItem('constraints', parameterData);
}

export async function updateModularParameter(parameterId, parameterData) {
    return updateItem('constraints', parameterId, parameterData);
}

export async function deleteModularParameter(parameterId) {
    return deleteItem('constraints', parameterId);
}

// --- Hardware Rule CRUD ---
export async function fetchHardwareRules(modularProductId = null, ruleId = null) {
    if (ruleId) {
        return fetchItem('hardware-rules', ruleId);
    }
    let url = `${MODULAR_API_BASE}/hardware-rules/`;
    if (modularProductId) {
        url += `?modular_product=${modularProductId}`; // Filter by product ID
    }
    return performApiRequest(url, 'GET');
}

export async function createHardwareRule(ruleData) {
    return createItem('hardware-rules', ruleData);
}

export async function updateHardwareRule(ruleId, ruleData) {
    return updateItem('hardware-rules', ruleId, ruleData);
}

export async function deleteHardwareRule(ruleId) {
    return deleteItem('hardware-rules', ruleId);
}

// --- Quote Request CRUD (New) ---
export async function fetchQuoteRequests() {
    return fetchAll('quotes');
}

export async function fetchQuoteRequestDetail(quoteId) {
    return fetchItem('quote-requests', quoteId);
}

export async function createQuoteRequest(quoteData) {
    return createItem('quote-requests', quoteData);
}

export async function deleteQuoteRequest(quoteId) {
    return deleteItem('quote-requests', quoteId);
}

// --- Material & Hardware Lookups (using MATERIAL_API_BASE) ---

export async function fetchWoodMaterials() {
    const url = `${MATERIAL_API_BASE}/woodens/`;
    return performApiRequest(url, 'GET');
}

export async function fetchEdgeBandMaterials() {
    const url = `${MATERIAL_API_BASE}/edgebands/`;
    return performApiRequest(url, 'GET');
}

export async function fetchAllHardware() {
    const url = `${MATERIAL_API_BASE}/hardware/`;
    return performApiRequest(url, 'GET');
}

export async function fetchAllHardwareGroups() {
    const url = `${MATERIAL_API_BASE}/hardware-groups/`;
    return performApiRequest(url, 'GET');
}

export async function fetchAllCategories() {
    const url = `${MATERIAL_API_BASE}/categories/`;
    return performApiRequest(url, 'GET');
}

export async function fetchAllCategoryTypes() {
    const url = `${MATERIAL_API_BASE}/category-types/`;
    return performApiRequest(url, 'GET');
}

export async function fetchAllCategoryModels() {
    const url = `${MATERIAL_API_BASE}/category-models/`;
    return performApiRequest(url, 'GET');
}