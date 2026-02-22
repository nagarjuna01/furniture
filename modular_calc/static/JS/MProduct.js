
    // ==============================
// Global State
// ==============================
const mpState = {
    page: 1,
    limit: 16,    
    lastPage: 1,
    category: "",
    type: "",
    model: "",
    search: ""
};

let allCategories = [];
let allTypes = [];
let allModels = [];

let tableSort = {
    categories: { field: null, direction: 1 },
    types:      { field: null, direction: 1 },
    models:     { field: null, direction: 1 }
};

let currentCategoryPage = 1;
let currentTypePage = 1;
let currentModelPage = 1;

// ==============================
// API Endpoints
// ==============================
const api = {
    categories: "/modularcalc/api/product-categories/",
    types: "/modularcalc/api/product-types/",
    models: "/modularcalc/api/product-models/",
    products: "/modularcalc/api/products/"
};

// ==============================
// Fetch All Pages Utility
// ==============================
async function fetchAllPages(url) {
    let results = [];
    let nextUrl = url;

    while (nextUrl) {
        try {
            const res = await fetch(nextUrl);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            if (data.results) results.push(...data.results);
            nextUrl = data.next;
        } catch (err) {
            console.error("Error fetching", nextUrl, err);
            nextUrl = null;
        }
    }
    return results;
}

// ==============================
// Preload reference data
// ==============================
async function preloadReferenceData() {
    try {
        [allCategories, allTypes, allModels] = await Promise.all([
            fetchAllPages(api.categories),
            fetchAllPages(api.types),
            fetchAllPages(api.models)
        ]);
        renderCategoryTable();
        renderTypeTable();
        renderModelTable();
        loadCategoriesDropdown(["mp-filter-category"]);
    } catch (err) {
        console.error("Failed to preload reference data:", err);
        showToast("Failed to load reference data", "danger");

    }
}

// ==============================
// Modular Products
// ==============================
async function apiGet(url, params = {}) {
    const fullUrl = new URL(url, window.location.origin);
    Object.keys(params).forEach(k => params[k] && fullUrl.searchParams.append(k, params[k]));
    const res = await fetch(fullUrl);
    return res.json();
}

async function loadModularProducts() {
    const data = await apiGet(api.products, {
        page: mpState.page,
        page_size: mpState.pageSize,
        category: mpState.category,
        type: mpState.type,
        model: mpState.model,
        search: mpState.search
    });

    mpState.lastPage = Math.ceil(data.count / mpState.pageSize);
    renderProducts(data.results);
}
function renderProducts(products) {
    const container = document.getElementById("product-list-container");
    if (!products || !products.length) {
        container.innerHTML = "<div class='col-12 text-center p-5'>No products found.</div>";
        return;
    }

    container.innerHTML = products.map(product => `
    <div class="col-xl-3 col-lg-4 col-md-6 mb-4"> <div class="card h-100 shadow-sm border-0">
            <div class="card-body d-flex flex-column p-3">
                <h6 class="card-title fw-bold text-dark mb-1 text-truncate" title="${product.name}">
                    ${product.name}
                </h6>
                
                <p class="mb-3">
                    <small class="text-muted" style="font-size: 0.7rem;">
                        <span class="text-primary">${product.category_name || 'Cat'}</span> | 
                        ${product.type_name || 'Type'} | 
                        ${product.productmodel_name || 'Mod'}
                    </small>
                </p>
                
                <div class="mt-auto pt-2 border-top">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                         <a href="/modularcalc/output/?product_id=${product.id}" class="btn btn-success btn-sm w-100 fw-bold py-1"> GET QUOTE</a>
                    </div>
                    <div class="btn-group w-100 shadow-sm">
                        <button class="btn btn-outline-info btn-sm view-btn" data-id="${product.id}"><i class="fas fa-eye"></i></button>
                        <button class="btn btn-outline-secondary btn-sm edit-btn" data-id="${product.id}"><i class="fas fa-edit"></i></button>
                        <button class="btn btn-outline-secondary btn-sm duplicate-btn" data-id="${product.id}"><i class="fas fa-copy"></i></button>
                        <button class="btn btn-outline-danger btn-sm delete-btn" data-id="${product.id}"><i class="fas fa-trash"></i></button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `).join("");
}

// Pagination buttons
document.getElementById("mp-next-page").addEventListener("click", () => {
    if (mpState.page < mpState.lastPage) { mpState.page++; loadModularProducts(); }
});
document.getElementById("mp-prev-page").addEventListener("click", () => {
    if (mpState.page > 1) { mpState.page--; loadModularProducts(); }
});
// Step 1: Open Input Modal
document.addEventListener('click', async function(e) {
    if (e.target.closest('.open-calc-modal')) {
        const btn = e.target.closest('.open-calc-modal');
        const productId = btn.dataset.id;
        
        document.getElementById('modal-product-id').value = productId;
        document.getElementById('target-product-name').innerText = btn.dataset.name;

        const res = await fetch(`/modularcalc/api/products/${productId}/`);
        const product = await res.json();
        const materialSelect = document.getElementById('m-material-select');
        
        // CONTEXT FIX: In your JSON, whitelist is inside part_templates[0]
        if (materialSelect && product.part_templates && product.part_templates.length > 0) {
            const whitelist = product.part_templates[0].material_whitelist;
            
            materialSelect.innerHTML = '<option value="" selected disabled>-- Choose Material --</option>' + 
                whitelist.map(m => `
                    <option value="${m.material}">
                        ${m.material_details.name} (${m.material_details.thickness_mm}mm)
                    </option>
                `).join('');
        }

        new bootstrap.Modal(document.getElementById('inputModal')).show();
    }
});

// MProduct.js -> Inside the 'run-engine-btn' click listener

// Search input
document.getElementById("mp-search").addEventListener("input", e => {
    mpState.search = e.target.value.trim();
    mpState.page = 1;
    loadModularProducts();
});
document.getElementById("show-add-product-btn").addEventListener("click", () => {
    window.location.href = "/modularcalc/addparts/";
});
async function viewProductDetails(productId) {
    try {
        const res = await fetch(`/modularcalc/api/products/${productId}/`);
        const product = await res.json();

        // Populate Modal Fields
        document.getElementById("showcase-title").innerText = product.name || "Unnamed";
        document.getElementById("showcase-category").innerText = product.category_name || "N/A";
        document.getElementById("showcase-type").innerText = product.type_name || "N/A";
        document.getElementById("showcase-model").innerText = product.productmodel || "N/A";
        document.getElementById("showcase-validation").innerText = product.product_validation_expression || "None";

        // Parameters Table
        document.getElementById("showcase-params-body").innerHTML = (product.parameters || []).map(p => `
            <tr><td>${p.name}</td><td>${p.abbreviation}</td><td>${p.default_value}</td><td>${p.description || ""}</td></tr>
        `).join("");

        // Parts Table
        document.getElementById("showcase-parts-body").innerHTML = (product.part_templates || []).map(pt => `
            <tr>
                <td><strong>${pt.name}</strong></td>
                <td><code>${pt.part_length_equation}</code></td>
                <td><code>${pt.part_width_equation}</code></td>
                <td>${pt.part_qty_equation}</td>
            </tr>
        `).join("");

        const modal = new bootstrap.Modal(document.getElementById('productShowcaseModal'));
        modal.show();
    } catch (err) {
        console.error("View Error:", err);
    }
}
/**
 * Maps incoming API data back to UI-friendly format for the Editor
 */
function applyDraftToUI(product) {
    console.log("Loading product into UI:", product);

    // 1. Basic Info
    const nameField = document.getElementById("product-name"); // Adjust IDs based on your actual HTML
    if (nameField) nameField.value = product.name || "";

    const descField = document.getElementById("product-description");
    if (descField) descField.value = product.description || "";

    // 2. Dimensions (The Cylinder Math)
    // Make sure these match your HTML input IDs
    if (document.getElementById("length_mm")) document.getElementById("length_mm").value = product.length_mm || 0;
    if (document.getElementById("width_mm")) document.getElementById("width_mm").value = product.width_mm || 0;
    if (document.getElementById("height_mm")) document.getElementById("height_mm").value = product.height_mm || 0;

    // 3. Dropdowns (Category/Type/Model)
    if (product.category) {
        const catSelect = document.getElementById("categoryselect");
        if (catSelect) {
            catSelect.value = product.category;
            // Trigger change to load dependent "Types"
            catSelect.dispatchEvent(new Event('change'));
        }
    }

    // 4. Validation Expression
    const validationField = document.getElementById("product-validation");
    if (validationField) validationField.value = product.product_validation_expression || "";

    showToast(`Loaded ${product.name} for editing`, "info");
}
// 2. EDIT: Load into Main Editor
function editProduct(productId) {
    if (!productId) {
        showToast("Invalid Product ID", "danger");
        return;
    }
    // Redirect to the builder page and pass the ID as a query parameter
    window.location.href = `/modularcalc/addparts/?edit_id=${productId}`;
}

// Ensure it is globally accessible for your click listeners
window.editProduct = editProduct;

document.addEventListener("click", async e => {
    // Find the closest button to handle clicks on the icon inside the button
    const target = e.target.closest('button');
    if (!target) return;

    const id = target.dataset.id;
    if (!id) return;

    // Route the action
    if (target.classList.contains("view-btn")) {
        viewProductDetails(id); // Opens your Showcase Modal
    } else if (target.classList.contains("edit-btn")) {
        editProduct(id); // Redirects to Builder
    } else if (target.classList.contains("delete-btn")) {
        deleteProduct(id); // Fires DELETE API
    } else if (target.classList.contains("duplicate-btn")) {
        duplicateProduct(id); // Fires Duplicate API
    }
});

// Ensure the function is global
window.viewProductDetails = viewProductDetails;
// ==============================
// Delete Product Logic
// ==============================
async function deleteProduct(id) {
    if (!confirm("🚨 Are you sure? Deleting this product will remove all its parts, rules, and configurations permanently.")) return;

    try {
        const res = await fetch(`${api.products}${id}/`, {
            method: "DELETE",
            headers: {
                "X-CSRFToken": window.CSRF_TOKEN,
                "Accept": "application/json"
            },
            credentials: "same-origin"
        });

        if (res.ok) {
            showToast("Product deleted successfully", "success");
            loadModularProducts(); // Refresh the grid
        } else {
            const data = await res.json();
            throw new Error(data.detail || "Delete failed");
        }
    } catch (err) {
        console.error("Delete Error:", err);
        showToast(err.message, "danger");
    }
}
// Expose to window for the HTML onclick/listeners
window.deleteProduct = deleteProduct;
/**
 * Maps incoming API data (snake_case) back to UI-friendly format
 */
/**
 * Main function to load a product into the editor for viewing/editing
 */

// Update your duplicateProduct function to catch the error body
async function duplicateProduct(productId) {
    try {
        const response = await fetch(`/modularcalc/api/products/${productId}/duplicate/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.CSRF_TOKEN 
            }
        });

        const data = await response.json();

        if (!response.ok) {
            // Log the specific validation errors (e.g., "duplicate key value violates unique constraint")
            console.error("Server Validation Errors:", data);
            
            // If the error is a dictionary (DRF style), flatten it for the alert/error
            let errorMessage = data.error || "Duplication failed";
            if (typeof data === 'object' && !data.error) {
                errorMessage = Object.entries(data)
                    .map(([key, val]) => `${key}: ${val}`)
                    .join(', ');
            }
            
            throw new Error(errorMessage);
        }

        console.log("Duplication Successful:", data);
        return data;
    } catch (error) {
        console.error("Duplicate Product Error:", error);
        throw error;
    }
}

async function getCalculatedMeasurements(productId, length, width, height) {
    const response = await fetch('/modularcalc/api/products/dry-run/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN },
        body: JSON.stringify({
            product_dims: { product_length: length, product_width: width, product_height: height },
            part_templates: [] // You fetch these from the product first
        })
    });
    const data = await response.json();
    console.log("Calculated Parts:", data.preview);
}
// ==============================
// Sorting Utility
// ==============================
function sortList(list, sortState) {
    if (!sortState.field) return list;
    return list.slice().sort((a,b) => {
        let x = a[sortState.field], y = b[sortState.field];
        if (x === undefined || y === undefined) return 0;
        x = typeof x === "string" ? x.toLowerCase() : x;
        y = typeof y === "string" ? y.toLowerCase() : y;
        if (x < y) return -1 * sortState.direction;
        if (x > y) return  1 * sortState.direction;
        return 0;
    });
}

// ==============================
// Tables rendering
// ==============================
function renderCategoryTable() {
    const searchTerm = document.getElementById("category-search").value.toLowerCase();
    let filtered = allCategories;
    if (searchTerm.length >= 3) filtered = allCategories.filter(c => c.name.toLowerCase().includes(searchTerm));
    filtered = sortList(filtered, tableSort.categories);

    const perPage = parseInt(document.getElementById("category-per-page").value) || 5;
    const totalPages = Math.ceil(filtered.length / perPage);
    if (currentCategoryPage > totalPages) currentCategoryPage = totalPages || 1;
    const start = (currentCategoryPage-1)*perPage;
    const paginated = filtered.slice(start,start+perPage);

    let html = "";
    paginated.forEach(c => {
        html += `
        <tr>
            <td>${c.name}</td>
            <td class="text-center">
                <button class="btn btn-sm btn-outline-warning me-1" onclick="editCategory(${c.id}, '${c.name}')"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteCategory(${c.id})"><i class="bi bi-trash"></i></button>
            </td>
        </tr>`;
    });
    document.getElementById("categoryTable").innerHTML = html;

    document.getElementById("category-prev").disabled = currentCategoryPage <= 1;
    document.getElementById("category-next").disabled = currentCategoryPage >= totalPages;
    document.getElementById("category-prev").onclick = () => { currentCategoryPage--; renderCategoryTable(); };
    document.getElementById("category-next").onclick = () => { currentCategoryPage++; renderCategoryTable(); };
}

document.getElementById("category-search").addEventListener("input", () => {
    currentCategoryPage = 1; // go back to first page
    renderCategoryTable();
});
function renderTypeTable() {
    const searchTerm = document.getElementById("type-search").value.toLowerCase();
    let filtered = allTypes;
    if (searchTerm.length >= 3) filtered = filtered.filter(t =>
        t.name.toLowerCase().includes(searchTerm) ||
        (t.category_name && t.category_name.toLowerCase().includes(searchTerm))
    );
    filtered = sortList(filtered, tableSort.types);

    const perPage = parseInt(document.getElementById("type-per-page").value) || 5;
    const totalPages = Math.ceil(filtered.length/perPage);
    if (currentTypePage>totalPages) currentTypePage=totalPages||1;
    const start=(currentTypePage-1)*perPage;
    const paginated=filtered.slice(start,start+perPage);

    let html="";
    paginated.forEach(t=>{
        html += `<tr>
            
            <td>${t.name}</td>
            <td>${t.category_name}</td>
            <td>
                <button class="btn btn-warning btn-sm" onclick="editType(${t.id}, '${t.name}', ${t.category})"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-danger btn-sm" onclick="deleteType(${t.id})"><i class="bi bi-trash"></button>
            </td>
        </tr>`;
    });
    document.getElementById("typeTable").innerHTML = html;
    document.getElementById("type-prev").disabled=currentTypePage<=1;
    document.getElementById("type-next").disabled=currentTypePage>=totalPages;
    document.getElementById("type-prev").onclick=()=>{currentTypePage--;renderTypeTable();};
    document.getElementById("type-next").onclick=()=>{currentTypePage++;renderTypeTable();};
}
document.getElementById("type-search").addEventListener("input", () => {
    currentTypePage = 1; // go back to first page when typing
    renderTypeTable();
});
function renderModelTable() {
    const searchTerm=document.getElementById("model-search").value.toLowerCase();
    let filtered=allModels;
    if(searchTerm.length>=3) filtered=filtered.filter(m=>m.name.toLowerCase().includes(searchTerm) || (m.type_name && m.type_name.toLowerCase().includes(searchTerm)));
    filtered=sortList(filtered, tableSort.models);

    const perPage=parseInt(document.getElementById("model-per-page").value)||5;
    const totalPages=Math.ceil(filtered.length/perPage);
    if(currentModelPage>totalPages) currentModelPage=totalPages||1;
    const start=(currentModelPage-1)*perPage;
    const paginated=filtered.slice(start,start+perPage);

    let html="";
    paginated.forEach(m=>{
        html+=`<tr>
            
            <td>${m.name}</td>
            <td>${m.type_name||""}</td>
            <td>
                <button class="btn btn-warning btn-sm" onclick="editModel(${m.id}, '${m.name}', ${m.type}, ${m.category})"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-danger btn-sm" onclick="deleteModel(${m.id})"><i class="bi bi-trash"></button>
            </td>
        </tr>`;
    });
    document.getElementById("modelTable").innerHTML=html;
    document.getElementById("model-prev").disabled=currentModelPage<=1;
    document.getElementById("model-next").disabled=currentModelPage>=totalPages;
    document.getElementById("model-prev").onclick=()=>{currentModelPage--;renderModelTable();};
    document.getElementById("model-next").onclick=()=>{currentModelPage++;renderModelTable();};
}
document.getElementById("model-search").addEventListener("input", () => {
    currentModelPage = 1; // reset page when searching
    renderModelTable();
});
// ==============================
// Dropdowns
// ==============================
async function loadCategoriesDropdown(extraIds=[]) {
    let html = `<option value="">Select Category</option>`;
    allCategories.forEach(c => html += `<option value="${c.id}">${c.name}</option>`);

    const targets = ["categoryselect","typeCategory","modelCategory"].concat(extraIds);
    targets.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = html;
    });

    return Promise.resolve();
}

async function loadTypesDropdownByCategory(categoryId, targetIds=[]) {
    const list = allTypes.filter(t => t.category == categoryId);
    let html = `<option value="">Select Type</option>`;
    list.forEach(t => html += `<option value="${t.id}">${t.name}</option>`);

    ["type-select","modelType"].concat(targetIds).forEach(id => {
        const el = document.getElementById(id);
        if (el) { el.innerHTML = html; el.disabled = false; }
    });

    return Promise.resolve();
}

async function loadModelsDropdownByType(typeId, targetIds=[]) {
    const list = allModels.filter(m => m.type == typeId);
    let html = `<option value="">Select Model</option>`;
    list.forEach(m => html += `<option value="${m.id}">${m.name}</option>`);

    ["model-select"].concat(targetIds).forEach(id => {
        const el = document.getElementById(id);
        if (el) { el.innerHTML = html; el.disabled = false; }
    });

    return Promise.resolve();
}

// ==============================
// Filters setup
// ==============================
function setupFilter(selectId, stateKey, loadDependentDropdown=null){
    const select=document.getElementById(selectId);
    select.addEventListener("change",async e=>{
        mpState[stateKey]=e.target.value;
        mpState.page=1;

        if(selectId==="mp-filter-category"){ mpState.type=""; mpState.model=""; }
        if(selectId==="mp-filter-type") mpState.model="";

        if(loadDependentDropdown) await loadDependentDropdown(mpState[stateKey]);

        document.getElementById("mp-filter-type").disabled=!mpState.category;
        document.getElementById("mp-filter-model").disabled=!mpState.type;

        loadModularProducts();
    });
}

// ==============================
// Init on page load
// ==============================
document.addEventListener("DOMContentLoaded", async () => {
    await preloadReferenceData();

    if (document.getElementById("categoryselect")) {
        initAddProductDropdowns(); // editor page
    }

    if (document.getElementById("mp-filter-category")) {
        setupFilter("mp-filter-category","category",
            c => loadTypesDropdownByCategory(c,["mp-filter-type"])
        );
        setupFilter("mp-filter-type","type",
            t => loadModelsDropdownByType(t,["mp-filter-model"])
        );
        setupFilter("mp-filter-model","model");

        loadModularProducts(); // list page only
    }
});

// ==============================
// Sorting click events
// ==============================
document.querySelectorAll(".sortable").forEach(h=>{
    h.style.cursor="pointer";
    h.addEventListener("click",()=>{
        const tab=h.dataset.tab, field=h.dataset.sort;
        let s=tableSort[tab];
        if(s.field===field) s.direction*=-1; else { s.field=field; s.direction=1; }

        if(tab==="categories") renderCategoryTable();
        if(tab==="types") renderTypeTable();
        if(tab==="models") renderModelTable();
    });
});
function openCategoryModal() {
    document.getElementById("categoryId").value = "";
    document.getElementById("categoryName").value = "";
    const modal = new bootstrap.Modal(document.getElementById("categoryModal"));
    modal.show();
}
function editCategory(id, name) {
    document.getElementById("categoryId").value = id;
    document.getElementById("categoryName").value = name;
    const modal = new bootstrap.Modal(document.getElementById("categoryModal"));
    modal.show();
}
function saveCategory(event) {
    event.preventDefault();
    const id = document.getElementById("categoryId").value;
    const name = document.getElementById("categoryName").value;

    const method = id ? "PUT" : "POST";
    const url = id ? api.categories + id + "/" : api.categories;

    console.log(`Saving category (${method}):`, name);

    fetch(url, {
        method: method,
        headers: { "Content-Type": "application/json",  "X-CSRFToken": window.CSRF_TOKEN },
        body: JSON.stringify({ name })
    })
    .then(res => res.json())
    .then(() => {
        console.log("Category saved successfully");
        document.getElementById("categoryForm").reset();
        bootstrap.Modal.getInstance(document.getElementById("categoryModal")).hide();
        preloadReferenceData();
    })
    .catch(err => console.error("Save Category Error:", err));
}
function deleteCategory(id) {
    if (!confirm("Are you sure you want to delete this category?")) return;
    console.log("Deleting category:", id);

    fetch(api.categories + id + "/", { method: "DELETE" , headers: {
            "X-CSRFToken": window.CSRF_TOKEN,
            "Accept": "application/json"
        },
        credentials: "same-origin"
    })
        .then(() => {
            
            preloadReferenceData();
        })
        .catch(err => console.error("Delete Category Error:", err));
}
function openTypeModal() {
  document.getElementById("typeId").value = "";
  document.getElementById("typeName").value = "";
  loadCategoriesDropdown();
  new bootstrap.Modal("#typeModal").show();
}

function editType(id, name, category) {
  document.getElementById("typeId").value = id;
  document.getElementById("typeName").value = name;
  loadCategoriesDropdown();

  setTimeout(() => {
    document.getElementById("typeCategory").value = category;
  }, 300);

  new bootstrap.Modal("#typeModal").show();
}

function saveType(e) {
  e.preventDefault();
  let id = document.getElementById("typeId").value;
  let payload = {
    name: document.getElementById("typeName").value,
    category: document.getElementById("typeCategory").value
  };

  fetch(id ? api.types + id + "/" : api.types, {
    method: id ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" , "X-CSRFToken": window.CSRF_TOKEN },
    body: JSON.stringify(payload)
  }).then(() => {
    bootstrap.Modal.getInstance(document.getElementById("typeModal")).hide();
    preloadReferenceData();
  });
}

function deleteType(id) {
    if (!confirm("Are you sure you want to delete this Type?")) return;

    fetch(`${api.types}${id}/`, { method: "DELETE" , headers: {
            "X-CSRFToken": window.CSRF_TOKEN,
            "Accept": "application/json"
        },
        credentials: "same-origin"
     })
        .then((res) => {
            if (!res.ok) {
                throw new Error(`Failed to delete type. HTTP ${res.status}`);
            }
            return preloadReferenceData();
        })
        .catch(err => {
            console.error("Delete Type Error:", err);
            alert("Failed to delete type. Check console for details.");
        });
}

async function openModelModal() {
  document.getElementById("modelId").value = "";
  document.getElementById("modelName").value = "";
  await loadCategoriesDropdown(); // wait for categories
  document.getElementById("modelType").innerHTML = ''; // clear type
  new bootstrap.Modal("#modelModal").show();
}

async function editModel(id, name, type, category) {
  document.getElementById("modelId").value = id;
  document.getElementById("modelName").value = name;

  await loadCategoriesDropdown();          // load categories
  document.getElementById("modelCategory").value = category; 

  await loadTypesDropdownByCategory(category); // load types for category
  document.getElementById("modelType").value = type;

  new bootstrap.Modal("#modelModal").show();
}
async function saveModel(e) {
  e.preventDefault();
  let id = document.getElementById("modelId").value;
  let payload = {
    name: document.getElementById("modelName").value,
    type: document.getElementById("modelType").value
  };

  await fetch(id ? api.models + id + "/" : api.models, {
    method: id ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" , "X-CSRFToken": window.CSRF_TOKEN},
    body: JSON.stringify(payload)
  });

  bootstrap.Modal.getInstance(document.getElementById("modelModal")).hide();

  // Prefetch all models to refresh table
  allModels = await fetchAllPages(api.models);
  preloadReferenceData();
}

async function deleteModel(id) {
    if (!confirm("Are you sure you want to delete this Model?")) return;

    try {
        const res = await fetch(`${api.models}${id}/`, { method: "DELETE" , headers: {
            "X-CSRFToken": window.CSRF_TOKEN,
            "Accept": "application/json"
        },
        credentials: "same-origin"});
        if (!res.ok) {
            throw new Error(`Failed to delete model. HTTP ${res.status}`);
        }

        await preloadReferenceData();   // refresh categories, types, models, dropdowns, tables

    } catch (err) {
        console.error("Delete Model Error:", err);
        alert("Failed to delete model. Check console for details.");
    }
}