// modular_dom.js 

// import { 
//     fetchModularProducts,
//     createModularProduct,
//     updateModularProduct,
//     deleteModularProduct
// } from './modular_api.js';

// import {
//     fetchModularParts,
//     createModularPart,
//     updateModularPart,
//     deleteModularPart,
//     fetchModularParameters,
//     createModularParameter,
//     updateModularParameter,
//     deleteModularParameter,
//     fetchWoodMaterials,
//     fetchEdgeBandMaterials
// } from './modular_api.js';

// document.addEventListener('DOMContentLoaded', () => {
//     // UI Elements
//     const loading = document.getElementById('loading');
//     const error = document.getElementById('error');
//     const container = document.getElementById('productCardsContainer');
//     const createButton = document.getElementById('createProductBtn');

//     // Modal Elements (for Modular Product)
//     const productModal = new bootstrap.Modal(document.getElementById('productModal'));
//     const modalTitle = document.getElementById('productModalLabel');
//     const productForm = document.getElementById('productForm');
//     const productIdInput = document.getElementById('productId');
//     const productNameInput = document.getElementById('productName');
//     const productValidationExpressionInput = document.getElementById('productValidationExpression');
    

//     // Validation Elements
//     const validateBtn = document.getElementById('validateBtn');
//     const testLengthInput = document.getElementById('testLength');
//     const testWidthInput = document.getElementById('testWidth');
//     const testHeightInput = document.getElementById('testHeight');
//     const validationResultDiv = document.getElementById('validationResult');

//     // New UI Elements for Parts & Parameters Modal
//     const partsParametersModal = new bootstrap.Modal(document.getElementById('partsParametersModal'));
//     const modalProductNameSpan = document.getElementById('modalProductName');
//     const addPartBtn = document.getElementById('addPartBtn');
//     const addParameterBtn = document.getElementById('addParameterBtn');
//     const partsListDiv = document.getElementById('partsList');
//     const parametersListDiv = document.getElementById('parametersList');
//     let currentProductId = null; // To store the ID of the product being managed

//     // New UI Elements for Part Form Modal
//     const partFormModal = new bootstrap.Modal(document.getElementById('partFormModal'));
//     const partForm = document.getElementById('partForm');
//     const partFormModalLabel = document.getElementById('partFormModalLabel');
//     const partIdInput = document.getElementById('partId');
//     const partProductIdInput = document.getElementById('partProductId');
//     const partNameInput = document.getElementById('partName');
//     const partLengthInput = document.getElementById('partLength');
//     const partWidthInput = document.getElementById('partWidth');
//     const partQtyInput = document.getElementById('partQty');
//     const partMaterialSelect = document.getElementById('partMaterial');
//     const partShapeSelect = document.getElementById('partShape');
//     const edgeTopSelect = document.getElementById('edgeTop');
//     const edgeBottomSelect = document.getElementById('edgeBottom');
//     const edgeLeftSelect = document.getElementById('edgeLeft');
//     const edgeRightSelect = document.getElementById('edgeRight');
//     const edgeCostInput = document.getElementById('edgeCost');
//     const grainDirectionSelect = document.getElementById('grainDirection');
//     const wastageMultiplierInput = document.getElementById('wastageMultiplier');

//     // New UI Elements for Parameter Form Modal
//     const parameterFormModal = new bootstrap.Modal(document.getElementById('parameterFormModal'));
//     const parameterForm = document.getElementById('parameterForm');
//     const parameterIdInput = document.getElementById('parameterId');
//     const parameterProductIdInput = document.getElementById('parameterProductId');
//     const parameterNameInput = document.getElementById('parameterName');
//     const parameterAbbreviationInput = document.getElementById('parameterAbbreviation');
//     const parameterValueInput = document.getElementById('parameterValue');

//     // Helper functions for UI state
//     function showLoading() {
//         loading.classList.remove('d-none');
//     }

//     function hideLoading() {
//         loading.classList.add('d-none');
//     }

//     function showError() {
//         error.classList.remove('d-none');
//     }

//     // Creates a complete DOM element for a product card
//     function createProductCard(product) {
//     const cardElement = document.createElement('div');
//     cardElement.className = 'col';
//     cardElement.setAttribute('data-id', product.id);

//     cardElement.innerHTML = `
//         <div class="card h-100 shadow-sm">
//             <div class="card-body">
//                 <h5 class="card-title">${product.name}</h5>
//                 <p class="card-text">
//                     <strong>Dimensions:</strong><br>
//                     ${product.length_mm} × ${product.width_mm} × ${product.height_mm} mm
//                 </p>
//                 <span class="badge bg-${product.status === 'published' ? 'success' : 'secondary'}">${product.status}</span>
                
//                 ${product.parts && product.parts.length > 0 ?
//                     `<div class="mt-2">
//                          <strong>Parts:</strong>
//                          <ul class="list-unstyled">
//                             ${product.parts.map(part => `<li>${part.name || 'Unnamed Part'}</li>`).join('')}
//                          </ul>
//                      </div>`
//                     : ''
//                 }
                
//                 ${product.product_validation_expression ?
//                     `<div class="mt-2 text-muted">
//                         <small><strong>Validation:</strong> ${product.product_validation_expression}</small>
//                     </div>`
//                     : ''
//                 }
//             </div>
//             <div class="card-footer text-muted d-flex justify-content-between align-items-center">
//                 <div class="text-start">
//                     <small>ID: ${product.id}</small><br>
//                     <small>Created: ${new Date(product.created_at).toLocaleDateString()}</small><br>
//                     <small>Updated: ${new Date(product.updated_at).toLocaleDateString()}</small>
//                 </div>
//                 <div class="btn-group" role="group">
//                     <button class="btn btn-sm btn-primary update-btn" type="button">Edit</button>
//                     <button class="btn btn-sm btn-danger delete-btn" type="button">Delete</button>
//                     <button class="btn btn-sm btn-secondary manage-btn" type="button">Manage</button>
//                 </div>
//             </div>
//         </div>
//     `;
    
//     // Attach event listeners to the buttons
//     const updateBtn = cardElement.querySelector('.update-btn');
//     const deleteBtn = cardElement.querySelector('.delete-btn');
//     const manageBtn = cardElement.querySelector('.manage-btn');

//     updateBtn.addEventListener('click', () => handleUpdate(product));
//     deleteBtn.addEventListener('click', () => handleDelete(product.id));
//     manageBtn.addEventListener('click', () => handleManage(product));

//     return cardElement;
// }

//     // Function to render all products
//     async function renderProducts() {
//         showLoading();
//         error.classList.add('d-none');
//         container.innerHTML = '';
//         try {
//             const data = await fetchModularProducts();
//             const products = data.results || [];
//             if (products.length === 0) {
//                 container.innerHTML = '<div class="col"><p class="text-muted">No products found.</p></div>';
//             } else {
//                 products.forEach(product => {
//                     const productCard = createProductCard(product);
//                     container.appendChild(productCard);
//                 });
//             }
//         } catch (err) {
//             showError();
//         } finally {
//             hideLoading();
//         }
//     }

//     // Modal Handlers
//     function showCreateModal() {
//         modalTitle.textContent = 'Add New Product';
//         productForm.reset();
//         productIdInput.value = '';
//         validationResultDiv.innerHTML = '';
//         productModal.show();
//     }
    
//     function showUpdateModal(product) {
//         modalTitle.textContent = 'Edit Product';
//         productIdInput.value = product.id;
//         productNameInput.value = product.name;
        
//         productValidationExpressionInput.value = product.product_validation_expression || '';
//         validationResultDiv.innerHTML = '';
//         testLengthInput.value = '';
//         testWidthInput.value = '';
//         testHeightInput.value = '';
//         productModal.show();
//     }

//     // CRUD functions
//     async function handleUpdate(product) {
//         showUpdateModal(product);
//     }

//     async function handleDelete(productId) {
//         if (confirm('Are you sure you want to delete this product?')) {
//             try {
//                 await deleteModularProduct(productId);
//                 alert('Product deleted successfully!');
//                 const cardToRemove = document.querySelector(`[data-id="${productId}"]`);
//                 if (cardToRemove) {
//                     cardToRemove.remove();
//                 }
//             } catch (err) {
//                 alert('Failed to delete product.');
//             }
//         }
//     }
    
//     // Function to safely validate the expression
//     function validateExpression(expression, l, w, h) {
//         const L = l;
//         const W = w;
//         const H = h;
//         const safeExpression = expression
//             .replace(/L/g, `(${L})`)
//             .replace(/W/g, `(${W})`)
//             .replace(/H/g, `(${H})`);

//         try {
//             return Function(`'use strict'; return (${safeExpression})`)();
//         } catch (e) {
//             console.error("Expression evaluation failed:", e);
//             return false;
//         }
//     }

//     // Handle form submission from the modal
//     productForm.addEventListener('submit', async (event) => {
//         event.preventDefault();
        
//         const productId = productIdInput.value;
//         const productData = {
//             name: productNameInput.value,
            
//             product_validation_expression: productValidationExpressionInput.value
//         };

//         try {
//             if (productId) {
//                 await updateModularProduct(productId, productData);
//                 alert('Product updated successfully!');
//             } else {
//                 await createModularProduct(productData);
//                 alert('Product created successfully!');
//             }
//             productModal.hide();
//             await renderProducts();
//         } catch (err) {
//             alert('Operation failed. Please check the console for details.');
//         }
//     });

//     // Handle "Validate" button click
//     validateBtn.addEventListener('click', () => {
//         const expression = productValidationExpressionInput.value;
//         const l = parseFloat(testLengthInput.value);
//         const w = parseFloat(testWidthInput.value);
//         const h = parseFloat(testHeightInput.value);

//         if (!expression || isNaN(l) || isNaN(w) || isNaN(h)) {
//             validationResultDiv.className = 'alert alert-warning';
//             validationResultDiv.textContent = 'Please provide an expression and all test dimensions.';
//             return;
//         }

//         const isValid = validateExpression(expression, l, w, h);

//         if (isValid) {
//             validationResultDiv.className = 'alert alert-success';
//             validationResultDiv.textContent = 'Validation successful! The dimensions pass the rule.';
//         } else {
//             validationResultDiv.className = 'alert alert-danger';
//             validationResultDiv.textContent = 'Validation failed. The dimensions do not pass the rule.';
//         }
//     });

//     // --- New Code for Parts and Parameters ---

//     // Function to handle opening the management modal
//     async function handleManage(product) {
//         currentProductId = product.id;
//         modalProductNameSpan.textContent = product.name;
        
//         partsParametersModal.show();
//         await loadPartsAndParameters();
//     }

//     // Function to load and render all parts and parameters for a product
//     async function loadPartsAndParameters() {
//         partsListDiv.innerHTML = '<p class="text-muted">Loading parts...</p>';
//         parametersListDiv.innerHTML = '<p class="text-muted">Loading parameters...</p>';

//         try {
//             // Fetch parts
//             const partsData = await fetchModularParts(currentProductId);
//             renderParts(partsData.results);
            
//             // Fetch parameters
//             const parametersData = await fetchModularParameters(currentProductId);
//             renderParameters(parametersData.results);
//         } catch (err) {
//             console.error('Failed to load parts or parameters:', err);
//             partsListDiv.innerHTML = '<p class="text-danger">Failed to load parts.</p>';
//             parametersListDiv.innerHTML = '<p class="text-danger">Failed to load parameters.</p>';
//         }
//     }

//     // Function to render the parts list
//     function renderParts(parts) {
//         partsListDiv.innerHTML = '';
//         if (parts.length === 0) {
//             partsListDiv.innerHTML = '<p class="text-muted">No parts configured yet.</p>';
//             return;
//         }

//         parts.forEach(part => {
//             const partElement = document.createElement('div');
//             partElement.className = 'alert alert-light border d-flex justify-content-between align-items-center';
//             partElement.innerHTML = `
//                 <span><strong>${part.name}</strong></span>
//                 <div>
//                     <button class="btn btn-sm btn-primary edit-part-btn" data-id="${part.id}">Edit</button>
//                     <button class="btn btn-sm btn-danger delete-part-btn" data-id="${part.id}">Delete</button>
//                 </div>
//             `;
//             partsListDiv.appendChild(partElement);
//         });

//         // Add event listeners for new buttons
//         partsListDiv.querySelectorAll('.edit-part-btn').forEach(btn => {
//             btn.addEventListener('click', () => handleEditPart(btn.dataset.id));
//         });
//         partsListDiv.querySelectorAll('.delete-part-btn').forEach(btn => {
//             btn.addEventListener('click', () => handleDeletePart(btn.dataset.id));
//         });
//     }

//     // Function to render the parameters list
//     function renderParameters(parameters) {
//         parametersListDiv.innerHTML = '';
//         if (parameters.length === 0) {
//             parametersListDiv.innerHTML = '<p class="text-muted">No parameters configured yet.</p>';
//             return;
//         }

//         parameters.forEach(param => {
//             const paramElement = document.createElement('div');
//             paramElement.className = 'alert alert-light border d-flex justify-content-between align-items-center';
//             paramElement.innerHTML = `
//                 <span><strong>${param.name}</strong> (${param.abbreviation}) = ${param.value}</span>
//                 <div>
//                     <button class="btn btn-sm btn-primary edit-param-btn" data-id="${param.id}">Edit</button>
//                     <button class="btn btn-sm btn-danger delete-param-btn" data-id="${param.id}">Delete</button>
//                 </div>
//             `;
//             parametersListDiv.appendChild(paramElement);
//         });

//         // Add event listeners for new buttons
//         parametersListDiv.querySelectorAll('.edit-param-btn').forEach(btn => {
//             btn.addEventListener('click', () => handleEditParameter(btn.dataset.id));
//         });
//         parametersListDiv.querySelectorAll('.delete-param-btn').forEach(btn => {
//             btn.addEventListener('click', () => handleDeleteParameter(btn.dataset.id));
//         });
//     }

//     // Handle button clicks for Parts
//     addPartBtn.addEventListener('click', async () => {
//         partFormModalLabel.textContent = 'Add New Part';
//         partForm.reset();
//         partIdInput.value = '';
//         partProductIdInput.value = currentProductId;
//         // Populate dropdowns before showing modal
//         await populateMaterialDropdowns();
//         populateGrainDirectionDropdown(); // Populate grain direction
//         partsParametersModal.hide();
//         partFormModal.show();
//     });

//     async function handleEditPart(partId) {
//         try {
//             // Fetch a single part's details
//             const part = await fetchModularParts(currentProductId, partId); // This should return the single part object directly if using a detail endpoint
            
//             if (part) {
//                 partFormModalLabel.textContent = 'Edit Part';
//                 partForm.reset();
//                 partIdInput.value = part.id;
//                 partProductIdInput.value = currentProductId;
                
//                 partNameInput.value = part.name;
//                 partLengthInput.value = part.part_length_equation;
//                 partWidthInput.value = part.part_width_equation;
//                 partQtyInput.value = part.part_qty_equation;
//                 partShapeSelect.value = part.part_shape;
//                 edgeCostInput.value = part.edge_band_grooving_cost;
//                 wastageMultiplierInput.value = part.shape_wastage_multiplier;
                
//                 // Populate and select dropdowns
//                 await populateMaterialDropdowns(part);
//                 populateGrainDirectionDropdown(part.grain_direction); // Populate and select grain direction

//                 partsParametersModal.hide();
//                 partFormModal.show();
//             }
//         } catch (err) {
//             console.error('Failed to fetch part details:', err);
//             alert('Failed to load part details. Please check the console.');
//         }
//     }

//     async function handleDeletePart(partId) {
//         if (confirm('Are you sure you want to delete this part?')) {
//             try {
//                 await deleteModularPart(partId);
//                 alert('Part deleted successfully!');
//                 await loadPartsAndParameters();
//             } catch (err) {
//                 alert('Failed to delete part.');
//             }
//         }
//     }

//     // Handle button clicks for Parameters
//     addParameterBtn.addEventListener('click', () => {
//         parameterFormModalLabel.textContent = 'Add New Parameter';
//         parameterForm.reset();
//         parameterIdInput.value = '';
//         parameterProductIdInput.value = currentProductId;
//         partsParametersModal.hide();
//         parameterFormModal.show();
//     });

//     async function handleEditParameter(paramId) {
//         try {
//             // Fetch a single parameter's details
//             const param = await fetchModularParameters(currentProductId, paramId); // This should return the single parameter object directly if using a detail endpoint
            
//             if (param) {
//                 parameterFormModalLabel.textContent = 'Edit Parameter';
//                 parameterIdInput.value = param.id;
//                 parameterProductIdInput.value = currentProductId;
//                 parameterNameInput.value = param.name;
//                 parameterAbbreviationInput.value = param.abbreviation;
//                 parameterValueInput.value = param.value;
//                 partsParametersModal.hide();
//                 parameterFormModal.show();
//             }
//         } catch (err) {
//             console.error('Failed to fetch parameter details:', err);
//             alert('Failed to load parameter details. Please check the console.');
//         }
//     }

//     async function handleDeleteParameter(paramId) {
//         if (confirm('Are you sure you want to delete this parameter?')) {
//             try {
//                 await deleteModularParameter(paramId);
//                 alert('Parameter deleted successfully!');
//                 await loadPartsAndParameters();
//             } catch (err) {
//                 alert('Failed to delete parameter.');
//             }
//         }
//     }

//     // Functions to populate dropdowns with API data
//     async function populateMaterialDropdowns(part = null) {
//         try {
//             const woodMaterials = (await fetchWoodMaterials()).results || [];
//             const edgeBandMaterials = (await fetchEdgeBandMaterials()).results || [];

//             // Populate Part Material dropdown
//             partMaterialSelect.innerHTML = '<option value="">-- Select Material --</option>';
//             woodMaterials.forEach(material => {
//                 const option = document.createElement('option');
//                 option.value = material.id;
//                 option.textContent = material.name; // Use material.name for display
//                 partMaterialSelect.appendChild(option);
//             });
//             if (part && part.part_material) {
//                 partMaterialSelect.value = part.part_material;
//             }

//             // Populate Edge Banding dropdowns
//             const edgeSelects = [edgeTopSelect, edgeBottomSelect, edgeLeftSelect, edgeRightSelect];
//             edgeSelects.forEach(select => {
//                 select.innerHTML = '<option value="">-- Select Edge --</option>';
//                 edgeBandMaterials.forEach(material => {
//                     const option = document.createElement('option');
//                     option.value = material.id;
//                     option.textContent = material.display_name; // Use material.display_name for display
//                     select.appendChild(option);
//                 });
//             });

//             if (part) {
//                 if (part.part_edgematerial_top) edgeTopSelect.value = part.part_edgematerial_top;
//                 if (part.part_edgematerial_bottom) edgeBottomSelect.value = part.part_edgematerial_bottom;
//                 if (part.part_edgematerial_left) edgeLeftSelect.value = part.part_edgematerial_left;
//                 if (part.part_edgematerial_right) edgeRightSelect.value = part.part_edgematerial_right;
//             }
//         } catch (err) {
//             console.error('Failed to populate material dropdowns:', err);
//             alert('Failed to load materials. Please check API connections.');
//         }
//     }

//     // Function to populate Grain Direction dropdown
//     function populateGrainDirectionDropdown(currentValue = null) {
//         const grainChoices = [
//             { value: 'none', text: 'No Grain' },
//             { value: 'horizontal', text: 'Horizontal' },
//             { value: 'vertical', text: 'Vertical' }
//         ];

//         grainDirectionSelect.innerHTML = ''; // Clear existing options
//         grainChoices.forEach(choice => {
//             const option = document.createElement('option');
//             option.value = choice.value;
//             option.textContent = choice.text;
//             grainDirectionSelect.appendChild(option);
//         });

//         if (currentValue) {
//             grainDirectionSelect.value = currentValue;
//         } else {
//             grainDirectionSelect.value = 'none'; // Default
//         }
//     }


//     // Handle Part Form Submission
//     partForm.addEventListener('submit', async (event) => {
//         event.preventDefault();
//         const partId = partIdInput.value;
//         const partData = {
//             modular_product: parseInt(partProductIdInput.value),
//             name: partNameInput.value,
//             part_length_equation: partLengthInput.value,
//             part_width_equation: partWidthInput.value,
//             part_qty_equation: partQtyInput.value,
//             part_material: partMaterialSelect.value ? parseInt(partMaterialSelect.value) : null, // Ensure null if not selected
//             part_shape: partShapeSelect.value,
//             part_edgematerial_top: edgeTopSelect.value ? parseInt(edgeTopSelect.value) : null,
//             part_edgematerial_bottom: edgeBottomSelect.value ? parseInt(edgeBottomSelect.value) : null,
//             part_edgematerial_left: edgeLeftSelect.value ? parseInt(edgeLeftSelect.value) : null,
//             part_edgematerial_right: edgeRightSelect.value ? parseInt(edgeRightSelect.value) : null,
//             edge_band_grooving_cost: parseFloat(edgeCostInput.value) || 0,
//             grain_direction: grainDirectionSelect.value,
//             shape_wastage_multiplier: parseFloat(wastageMultiplierInput.value) || 1.0,
//         };

//         try {
//             if (partId) {
//                 await updateModularPart(partId, partData);
//                 alert('Part updated successfully!');
//             } else {
//                 await createModularPart(partData);
//                 alert('Part created successfully!');
//             }
//             partFormModal.hide();
//             await loadPartsAndParameters();
//             partsParametersModal.show();
//         } catch (err) {
//             alert('Operation failed. Please check the console for details.');
//         }
//     });

//     // Handle Parameter Form Submission
//     parameterForm.addEventListener('submit', async (event) => {
//         event.preventDefault();
//         const parameterId = parameterIdInput.value;
//         const parameterData = {
//             modular_product: parseInt(parameterProductIdInput.value),
//             name: parameterNameInput.value,
//             abbreviation: parameterAbbreviationInput.value,
//             value: parseFloat(parameterValueInput.value),
//         };

//         try {
//             if (parameterId) {
//                 await updateModularParameter(parameterId, parameterData);
//                 alert('Parameter updated successfully!');
//             } else {
//                 await createModularParameter(parameterData);
//                 alert('Parameter created successfully!');
//             }
//             parameterFormModal.hide();
//             await loadPartsAndParameters();
//             partsParametersModal.show();
//         } catch (err) {
//             alert('Operation failed. Please check the console for details.');
//         }
//     });

//     // Attach event listeners
//     if (createButton) {
//         createButton.addEventListener('click', showCreateModal);
//     }
    
//     // Initial data load
//     renderProducts();
// });
// import { 
//     fetchAll, fetchItem,
//     fetchModularProducts, createModularProduct, updateModularProduct, deleteModularProduct,
//     fetchModularParts, createModularPart, updateModularPart, deleteModularPart,
//     fetchModularParameters, createModularParameter, updateModularParameter, deleteModularParameter,
//     fetchWoodMaterials, fetchEdgeBandMaterials, fetchAllHardware,
//     fetchAllCategories, fetchAllCategoryTypes, fetchAllCategoryModels
// } from './modular_api.js';

// // --- Global DOM Elements ---
// const loadingDiv = document.getElementById("loading");
// const errorDiv = document.getElementById("error");
// const productCardsContainer = document.getElementById("productCardsContainer");
// const createProductBtn = document.getElementById("createProductBtn");

// // Product Modal Elements
// const productModal = new bootstrap.Modal(document.getElementById("productModal"));
// const productForm = document.getElementById("productForm");
// const productIdInput = document.getElementById("productId");
// const productNameInput = document.getElementById("productName");
// const productDescriptionInput = document.getElementById("productDescription");
// const productValidationExpressionInput = document.getElementById("productValidationExpression");
// const productIsStandardInput = document.getElementById("productIsStandard");
// const productIsActiveInput = document.getElementById("productIsActive");

// // Parts/Parameters Modal Elements
// const partsParametersModal = new bootstrap.Modal(document.getElementById("partsParametersModal"));
// const modalProductName = document.getElementById("modalProductName");
// const partsList = document.getElementById("partsList");
// const addPartBtn = document.getElementById("addPartBtn");
// const parametersList = document.getElementById("parametersList");
// const addParameterBtn = document.getElementById("addParameterBtn");

// // Part Form Container (Now on the main page)
// const partFormContainer = document.getElementById("partFormContainer");
// const partForm = document.getElementById("partForm");
// const partFormTitle = document.getElementById("partFormTitle");
// const closePartFormBtn = document.getElementById("closePartFormBtn");
// const cancelPartFormBtn = document.getElementById("cancelPartFormBtn");
// const partIdInput = document.getElementById("partId");
// const partProductIdInput = document.getElementById("partProductId");
// const partNameInput = document.getElementById("partName"); 
// const partLengthInput = document.getElementById("partLength");
// const partWidthInput = document.getElementById("partWidth");
// const partQtyInput = document.getElementById("partQty");
// const partShapeInput = document.getElementById("partShape");
// const grainDirectionInput = document.getElementById("grainDirection");
// const wastageMultiplierInput = document.getElementById("wastageMultiplier");
// const edgeTopInput = document.getElementById("edgeTop");
// const edgeBottomInput = document.getElementById("edgeBottom");
// const edgeLeftInput = document.getElementById("edgeLeft");
// const edgeRightInput = document.getElementById("edgeRight");
// const edgeCostInput = document.getElementById("edgeCost");

// // New Material Tree View Containers
// const materialTreeContainer = document.getElementById("materialTree");
// const compatibleWoodsListContainer = document.getElementById("compatibleWoodsList").querySelector('ul');

// // Hardware requirements dynamic section
// const hardwareRequirementsContainer = document.getElementById("hardwareRequirementsContainer");
// const noHardwareMessage = document.getElementById("noHardwareMessage");
// const addHardwareRequirementBtn = document.getElementById("addHardwareRequirementBtn");

// // Parameter Form Modal Elements
// const parameterFormModal = new bootstrap.Modal(document.getElementById("parameterFormModal"));
// const parameterForm = document.getElementById("parameterForm");
// const parameterIdInput = document.getElementById("parameterId");
// const parameterProductIdInput = document.getElementById("parameterProductId");
// const parameterNameInput = document.getElementById("parameterName");
// const parameterAbbreviationInput = document.getElementById("parameterAbbreviation");
// const parameterValueInput = document.getElementById("parameterValue");


// // --- Global State ---
// let currentProductId = null;
// let allWoodMaterials = [];
// let allEdgeBandMaterials = [];
// let allCategories = [];
// let allTypes = [];
// let allModels = [];
// let allHardware = [];

// // To store the current selections for the tree view
// let selectedWoodIds = new Set();


// // --- Helper Functions ---

// const populateSelect = (selectElement, items, selectedIds = []) => {
//     selectElement.innerHTML = '';
    
//     if (!selectElement.multiple) {
//         const defaultOption = document.createElement('option');
//         defaultOption.value = '';
//         defaultOption.textContent = '--- Select ---';
//         selectElement.appendChild(defaultOption);
//     }

//     items.forEach(item => {
//         const option = document.createElement('option');
//         option.value = item.id;
//         option.textContent = item.name;
//         if (selectedIds.includes(item.id)) {
//             option.selected = true;
//         }
//         selectElement.appendChild(option);
//     });
// };

// const createHardwareRequirementForm = (requirement = {}, allHardware) => {
//     const div = document.createElement('div');
//     div.classList.add('hardware-requirement-item', 'mb-3', 'p-3', 'border', 'rounded');
//     div.innerHTML = `
//         <input type="hidden" class="hardware-requirement-id" value="${requirement.id || ''}">
//         <div class="row g-2 align-items-end">
//             <div class="col-md-6">
//                 <label class="form-label">Hardware</label>
//                 <select class="form-select hardware-select" required></select>
//             </div>
//             <div class="col-md-5">
//                 <label class="form-label">Quantity Equation</label>
//                 <input type="text" class="form-control hardware-equation" value="${requirement.equation || ''}" placeholder="e.g., L / 100">
//             </div>
//             <div class="col-md-1">
//                 <button type="button" class="btn btn-danger btn-sm remove-hardware-requirement-btn">X</button>
//             </div>
//         </div>
//     `;
    
//     const hardwareSelect = div.querySelector('.hardware-select');
//     populateSelect(hardwareSelect, allHardware, requirement.hardware ? [requirement.hardware] : []);
    
//     if (requirement.hardware) {
//         hardwareSelect.value = requirement.hardware;
//     }

//     div.querySelector('.remove-hardware-requirement-btn').addEventListener('click', () => {
//         div.remove();
//         if (hardwareRequirementsContainer.children.length === 1) {
//             noHardwareMessage.classList.remove('d-none');
//         }
//     });

//     return div;
// };

// // --- Main Product CRUD ---

// const renderProductCard = (product) => {
//     const cardHtml = `
//         <div class="col" data-product-id="${product.id}">
//             <div class="card h-100">
//                 <div class="card-body">
//                     <h5 class="card-title">${product.name}</h5>
//                     <p class="card-text">
//                         Description: ${product.description || 'N/A'}<br>
//                         Validation: ${product.validation_expression || 'None'}
//                     </p>
//                 </div>
//                 <div class="card-footer d-flex justify-content-between">
//                     <button class="btn btn-sm btn-info edit-btn">Edit</button>
//                     <button class="btn btn-sm btn-primary manage-parts-btn">Manage Parts & Parameters</button>
//                     <button class="btn btn-sm btn-danger delete-btn">Delete</button>
//                 </div>
//             </div>
//         </div>
//     `;
//     productCardsContainer.insertAdjacentHTML('beforeend', cardHtml);
// };

// const loadProducts = async () => {
//     loadingDiv.classList.remove("d-none");
//     errorDiv.classList.add("d-none");
//     productCardsContainer.innerHTML = '';
    
//     try {
//         const data = await fetchModularProducts();
//         const products = data.results;
        
//         if (products.length === 0) {
//             productCardsContainer.innerHTML = "<p class='text-muted'>No modular products found.</p>";
//         } else {
//             products.forEach(renderProductCard);
//         }
//     } catch (error) {
//         errorDiv.classList.remove("d-dne");
//         errorDiv.textContent = "Failed to load products. Please try again.";
//         console.error(error);
//     } finally {
//         loadingDiv.classList.add("d-none");
//     }
// };

// document.addEventListener("DOMContentLoaded", loadProducts);

// createProductBtn.addEventListener("click", () => {
//     productForm.reset();
//     productIdInput.value = "";
//     productModal.show();
// });

// productForm.addEventListener("submit", async (e) => {
//     e.preventDefault();
    
//     const productId = productIdInput.value;
//     const productData = {
//         name: productNameInput.value,
//         description: productDescriptionInput.value,
//         validation_expression: productValidationExpressionInput.value,
//         is_standard: productIsStandardInput.checked,
//         is_active: productIsActiveInput.checked,
//     };
    
//     try {
//         if (productId) {
//             await updateModularProduct(productId, productData);
//         } else {
//             await createModularProduct(productData);
//         }
//         productModal.hide();
//         await loadProducts();
//     } catch (error) {
//         alert("Failed to save product. " + error.message);
//     }
// });

// productCardsContainer.addEventListener("click", async (e) => {
//     const card = e.target.closest("[data-product-id]");
//     if (!card) return;

//     const productId = card.dataset.productId;
    
//     if (e.target.classList.contains("edit-btn")) {
//         try {
//             const product = await fetchItem("modular1", productId);
//             productIdInput.value = product.id;
//             productNameInput.value = product.name;
//             productDescriptionInput.value = product.description;
//             productValidationExpressionInput.value = product.validation_expression;
//             productIsStandardInput.checked = product.is_standard;
//             productIsActiveInput.checked = product.is_active;
//             productModal.show();
//         } catch (error) {
//             alert("Failed to load product data for editing.");
//         }
//     } else if (e.target.classList.contains("delete-btn")) {
//         if (confirm("Are you sure you want to delete this product?")) {
//             try {
//                 await deleteModularProduct(productId);
//                 await loadProducts();
//             } catch (error) {
//                 alert("Failed to delete product.");
//             }
//         }
//     } else if (e.target.classList.contains("manage-parts-btn")) {
//         currentProductId = productId;
//         const productName = card.querySelector(".card-title").textContent;
//         modalProductName.textContent = productName;
        
//         await loadPartsForProduct(productId);
//         await loadParametersForProduct(productId);
//         partsParametersModal.show();
//     }
// });


// // --- Part Management Logic ---

// const renderPartsList = (parts) => {
//     partsList.innerHTML = '';
//     if (parts.length === 0) {
//         partsList.innerHTML = "<p class='text-muted'>No parts configured yet.</p>";
//         return;
//     }
    
//     parts.forEach(part => {
//         const partItemHtml = `
//             <div class="card mb-2" data-part-id="${part.id}">
//                 <div class="card-body d-flex justify-content-between align-items-center">
//                     <div>
//                         <h6 class="mb-0">${part.name}</h6>
//                         <small class="text-muted">L: ${part.part_length_equation} | W: ${part.part_width_equation} | Qty: ${part.part_quantity_equation}</small>
//                     </div>
//                     <div>
//                         <button class="btn btn-sm btn-info edit-part-btn me-2">Edit</button>
//                         <button class="btn btn-sm btn-danger delete-part-btn">Delete</button>
//                     </div>
//                 </div>
//             </div>
//         `;
//         partsList.insertAdjacentHTML('beforeend', partItemHtml);
//     });
// };

// const loadPartsForProduct = async (productId) => {
//     try {
//         const data = await fetchModularParts(productId);
//         const parts = data.results;
//         renderPartsList(parts);
//     } catch (error) {
//         partsList.innerHTML = "<p class='text-danger'>Failed to load parts.</p>";
//         console.error(error);
//     }
// };

// const getWoodIdsForHierarchy = (type, id) => {
//     const woodIds = new Set();
//     const parsedId = parseInt(id);

//     if (type === 'wood') {
//         woodIds.add(parsedId);
//     } else if (type === 'model') {
//         // CORRECTED: w.category_model -> w.material_model
//         allWoodMaterials.filter(w => w.material_model && w.material_model.id === parsedId).forEach(w => woodIds.add(w.id));
//     } else if (type === 'type') {
//         // CORRECTED: w.category_type -> w.material_type, and !w.category_model -> !w.material_model
//         allWoodMaterials.filter(w => w.material_type && w.material_type.id === parsedId && !w.material_model).forEach(w => woodIds.add(w.id));
        
//         // CORRECTED: m.category_type -> m.model_category
//         const modelsInType = allModels.filter(m => m.model_category && m.model_category.id === parsedId);
//         modelsInType.forEach(model => {
//             // CORRECTED: w.category_model -> w.material_model
//             allWoodMaterials.filter(w => w.material_model && w.material_model.id === model.id).forEach(w => woodIds.add(w.id));
//         });
//     } else if (type === 'category') {
//         // CORRECTED: w.category -> w.material_grp, and !w.category_type -> !w.material_type
//         allWoodMaterials.filter(w => w.material_grp && w.material_grp.id === parsedId && !w.material_type).forEach(w => woodIds.add(w.id));
        
//         const typesInCategory = allTypes.filter(t => t.category && t.category.id === parsedId);
//         typesInCategory.forEach(type => {
//             // CORRECTED: w.category_type -> w.material_type, and !w.category_model -> !w.material_model
//             allWoodMaterials.filter(w => w.material_type && w.material_type.id === type.id && !w.material_model).forEach(w => woodIds.add(w.id));
            
//             // CORRECTED: m.category_type -> m.model_category
//             const modelsInType = allModels.filter(m => m.model_category && m.model_category.id === type.id);
//             modelsInType.forEach(model => {
//                 // CORRECTED: w.category_model -> w.material_model
//                 allWoodMaterials.filter(w => w.material_model && w.material_model.id === model.id).forEach(w => woodIds.add(w.id));
//             });
//         });
//     }
//     return woodIds;
// };

// // --- New Tree View Material Selection Logic ---

// const updateSelectedWoodsList = () => {
//     compatibleWoodsListContainer.innerHTML = '';
//     if (selectedWoodIds.size === 0) {
//         compatibleWoodsListContainer.innerHTML = "<li class='text-muted'>No woods selected.</li>";
//         return;
//     }

//     const woodsToDisplay = Array.from(selectedWoodIds).map(id => allWoodMaterials.find(w => w.id === id)).filter(Boolean);
//     woodsToDisplay.sort((a,b) => a.name.localeCompare(b.name));
    
//     woodsToDisplay.forEach(wood => {
//         const li = document.createElement('li');
//         li.textContent = wood.name;
//         li.classList.add('py-1');
//         compatibleWoodsListContainer.appendChild(li);
//     });
// };
// const handleCheckboxChange = (event) => {
//     const checkbox = event.target;
//     const parentLi = checkbox.closest('li');
//     const type = parentLi.dataset.type;
//     const id = parentLi.dataset.id;
//     const isChecked = checkbox.checked;

//     const woodsToToggle = getWoodIdsForHierarchy(type, id);

//     woodsToToggle.forEach(woodId => {
//         if (isChecked) {
//             selectedWoodIds.add(woodId);
//         } else {
//             selectedWoodIds.delete(woodId);
//         }
//     });

//     const childCheckboxes = parentLi.querySelectorAll('input[type="checkbox"]');
//     childCheckboxes.forEach(childCheckbox => {
//         childCheckbox.checked = isChecked;
//     });
    
//     updateSelectedWoodsList();
// };
// const handleTreeItemClick = (event) => {
//     const target = event.target;
//     const parentLi = target.closest('li');

//     if (target.classList.contains('expand-toggle')) {
//         const nestedList = parentLi.querySelector('ul');
//         if (nestedList) {
//             nestedList.classList.toggle('d-none');
//             target.textContent = nestedList.classList.contains('d-none') ? '+' : '-';
//         }
//     }
// };
// const renderMaterialTree = (initialSelectionIds = new Set()) => {
//     selectedWoodIds = initialSelectionIds;
//     materialTreeContainer.innerHTML = '';
//     const mainUl = document.createElement('ul');
//     mainUl.classList.add('list-unstyled', 'm-0');

//     allCategories.forEach(category => {
//         const categoryLi = document.createElement('li');
//         categoryLi.classList.add('py-1', 'ps-1');
        
//         const typesInCat = allTypes.filter(t => t.category && t.category.id === category.id);
//         // CORRECTED: w.category -> w.material_grp
//         const woodsInCat = allWoodMaterials.filter(w => w.material_grp && w.material_grp.id === category.id && !w.material_type); // Also changed !w.category_type to !w.material_type for consistency
//         const hasChildren = typesInCat.length > 0 || woodsInCat.length > 0;
//         const toggleSpan = hasChildren ? `<span class="expand-toggle me-2 fw-bold cursor-pointer">+</span>` : `<span class="me-2 invisible">-</span>`;
//         const categoryChecked = [...getWoodIdsForHierarchy('category', category.id)].every(id => selectedWoodIds.has(id)) && selectedWoodIds.size > 0;
        
//         categoryLi.innerHTML = `
//             ${toggleSpan}
//             <input type="checkbox" id="cat-${category.id}" class="form-check-input me-1" data-type="category" data-id="${category.id}" ${categoryChecked ? 'checked' : ''}>
//             <label for="cat-${category.id}" class="form-check-label">${category.name}</label>
//         `;

//         if (hasChildren) {
//             const nestedUl = document.createElement('ul');
//             nestedUl.classList.add('list-unstyled', 'ps-4', 'm-0', 'd-none');
            
//             woodsInCat.forEach(wood => {
//                 const woodLi = document.createElement('li');
//                 woodLi.classList.add('py-1', 'ps-1');
//                 woodLi.dataset.type = 'wood';
//                 woodLi.dataset.id = wood.id;
//                 woodLi.innerHTML = `<input type="checkbox" id="wood-${wood.id}" class="form-check-input me-1" data-type="wood" data-id="${wood.id}" ${selectedWoodIds.has(wood.id) ? 'checked' : ''}><label for="wood-${wood.id}" class="form-check-label">${wood.name}</label>`;
//                 nestedUl.appendChild(woodLi);
//             });

//             typesInCat.forEach(type => {
//                 console.log(`Processing Type: ${type.name} (ID: ${type.id})`);
//                 const typeLi = document.createElement('li');
//                 typeLi.classList.add('py-1', 'ps-1');
                
//                 // CORRECTED: m.category_type -> m.model_category
//                 const modelsInType = allModels.filter(m => m.model_category && m.model_category.id === type.id);
//                 // CORRECTED: w.category_type -> w.material_type, and !w.category_model -> !w.material_model
//                 const woodsInType = allWoodMaterials.filter(w => w.material_type && w.material_type.id === type.id && !w.material_model);
//                 const hasTypeChildren = modelsInType.length > 0 || woodsInType.length > 0;
//                 const typeToggle = hasTypeChildren ? `<span class="expand-toggle me-2 fw-bold cursor-pointer">+</span>` : `<span class="me-2 invisible">-</span>`;
//                 const typeChecked = [...getWoodIdsForHierarchy('type', type.id)].every(id => selectedWoodIds.has(id)) && selectedWoodIds.size > 0;

//                 typeLi.innerHTML = `
//                     ${typeToggle}
//                     <input type="checkbox" id="type-${type.id}" class="form-check-input me-1" data-type="type" data-id="${type.id}" ${typeChecked ? 'checked' : ''}>
//                     <label for="type-${type.id}" class="form-check-label">${type.name}</label>
//                 `;

//                 if (hasTypeChildren) {
//                     const nestedTypeUl = document.createElement('ul');
//                     nestedTypeUl.classList.add('list-unstyled', 'ps-4', 'm-0', 'd-none');

//                     woodsInType.forEach(wood => {
//                         const woodLi = document.createElement('li');
//                         woodLi.classList.add('py-1', 'ps-1');
//                         woodLi.dataset.type = 'wood';
//                         woodLi.dataset.id = wood.id;
//                         woodLi.innerHTML = `<input type="checkbox" id="wood-${wood.id}" class="form-check-input me-1" data-type="wood" data-id="${wood.id}" ${selectedWoodIds.has(wood.id) ? 'checked' : ''}><label for="wood-${wood.id}" class="form-check-label">${wood.name}</label>`;
//                         nestedTypeUl.appendChild(woodLi);
//                     });

//                     modelsInType.forEach(model => {
//                         const modelLi = document.createElement('li');
//                         modelLi.classList.add('py-1', 'ps-1');
                        
//                         // CORRECTED: w.category_model -> w.material_model
//                         const woodsInModel = allWoodMaterials.filter(w => w.material_model && w.material_model.id === model.id);
//                         const hasModelChildren = woodsInModel.length > 0;
//                         const modelToggle = hasModelChildren ? `<span class="expand-toggle me-2 fw-bold cursor-pointer">+</span>` : `<span class="me-2 invisible">-</span>`;
//                         const modelChecked = [...getWoodIdsForHierarchy('model', model.id)].every(id => selectedWoodIds.has(id)) && selectedWoodIds.size > 0;

//                         modelLi.innerHTML = `
//                             ${modelToggle}
//                             <input type="checkbox" id="model-${model.id}" class="form-check-input me-1" data-type="model" data-id="${model.id}" ${modelChecked ? 'checked' : ''}>
//                             <label for="model-${model.id}" class="form-check-label">${model.name}</label>
//                         `;

//                         if (hasModelChildren) {
//                             const nestedModelUl = document.createElement('ul');
//                             nestedModelUl.classList.add('list-unstyled', 'ps-4', 'm-0', 'd-none');
//                             woodsInModel.forEach(wood => {
//                                 const woodLi = document.createElement('li');
//                                 woodLi.classList.add('py-1', 'ps-1');
//                                 woodLi.dataset.type = 'wood';
//                                 woodLi.dataset.id = wood.id;
//                                 woodLi.innerHTML = `<input type="checkbox" id="wood-${wood.id}" class="form-check-input me-1" data-type="wood" data-id="${wood.id}" ${selectedWoodIds.has(wood.id) ? 'checked' : ''}><label for="wood-${wood.id}" class="form-check-label">${wood.name}</label>`;
//                                 nestedModelUl.appendChild(woodLi);
//                             });
//                             modelLi.appendChild(nestedModelUl);
//                         }
//                         nestedTypeUl.appendChild(modelLi);
//                     });
//                     typeLi.appendChild(nestedTypeUl);
//                 }
//                 nestedUl.appendChild(typeLi);
//             });
//             categoryLi.appendChild(nestedUl);
//         }
//         mainUl.appendChild(categoryLi);
//     });

//     materialTreeContainer.appendChild(mainUl);

//     materialTreeContainer.addEventListener('change', handleCheckboxChange);
//     materialTreeContainer.addEventListener('click', handleTreeItemClick);
    
//     updateSelectedWoodsList();
// };
// const loadPartFormLookups = async (initialSelectionIds = new Set()) => {
//     try {
//         const woodData = await fetchWoodMaterials();
//         allWoodMaterials = woodData.results || woodData;
        
//         const edgeBandData = await fetchEdgeBandMaterials();
//         allEdgeBandMaterials = edgeBandData.results || edgeBandData;

//         const categoriesData = await fetchAllCategories();
//         allCategories = categoriesData.results || categoriesData;
        
//         const typesData = await fetchAllCategoryTypes();
//         allTypes = typesData.results || typesData;
        
//         const modelsData = await fetchAllCategoryModels();
//         allModels = modelsData.results || modelsData;
        
//         const hardwareData = await fetchAllHardware();
//         allHardware = (hardwareData.results || hardwareData).map(hw => ({
//             ...hw,
//             name: hw.h_name
//         }));
        
//         populateSelect(edgeTopInput, allEdgeBandMaterials);
//         populateSelect(edgeBottomInput, allEdgeBandMaterials);
//         populateSelect(edgeLeftInput, allEdgeBandMaterials);
//         populateSelect(edgeRightInput, allEdgeBandMaterials);

//         renderMaterialTree(initialSelectionIds);

//     } catch (error) {
//         console.error("Failed to load part form lookup data:", error);
//         alert("Failed to load necessary data for part form. Check console for details.");
//     }
// };

// addPartBtn.addEventListener("click", async () => {
//     partForm.reset();
//     partIdInput.value = "";
//     partProductIdInput.value = currentProductId;
//     partFormTitle.textContent = "Add New Part";
    
//     selectedWoodIds.clear();
//     hardwareRequirementsContainer.innerHTML = '';
//     noHardwareMessage.classList.remove('d-none');
    
//     await loadPartFormLookups();
//     partFormContainer.classList.remove("d-none");
//     partsParametersModal.hide(); // Hide the parts/parameters modal
//     partFormContainer.scrollIntoView({ behavior: 'smooth' });
// });

// closePartFormBtn.addEventListener('click', () => {
//     partFormContainer.classList.add("d-none");
// });

// cancelPartFormBtn.addEventListener('click', () => {
//     partFormContainer.classList.add("d-none");
// });

// addHardwareRequirementBtn.addEventListener('click', () => {
//     noHardwareMessage.classList.add('d-none');
//     const newHardwareForm = createHardwareRequirementForm({}, allHardware);
//     hardwareRequirementsContainer.appendChild(newHardwareForm);
// });


// partForm.addEventListener("submit", async (e) => {
//     e.preventDefault();
    
//     const partId = partIdInput.value;

//     const hardwareRequirements = [];
//     hardwareRequirementsContainer.querySelectorAll('.hardware-requirement-item').forEach(item => {
//         const reqId = item.querySelector('.hardware-requirement-id').value;
//         const hardwareId = item.querySelector('.hardware-select').value;
//         const equation = item.querySelector('.hardware-equation').value;

//         if (hardwareId && equation) {
//             hardwareRequirements.push({
//                 id: reqId || undefined,
//                 hardware: parseInt(hardwareId),
//                 equation: equation
//             });
//         }
//     });

//     const partData = {
//         name: partNameInput.value,
//         modular_product: parseInt(partProductIdInput.value),
//         part_length_equation: partLengthInput.value,
//         part_width_equation: partWidthInput.value,
//         part_quantity_equation: partQtyInput.value,
//         part_shape: partShapeInput.value,
//         grain_direction: grainDirectionInput.value,
//         shape_wastage_multiplier: parseFloat(wastageMultiplierInput.value),
//         edge_band_grooving_cost: parseFloat(edgeCostInput.value),
        
//         part_edgematerial_top: edgeTopInput.value ? parseInt(edgeTopInput.value) : null,
//         part_edgematerial_bottom: edgeBottomInput.value ? parseInt(edgeBottomInput.value) : null,
//         part_edgematerial_left: edgeLeftInput.value ? parseInt(edgeLeftInput.value) : null,
//         part_edgematerial_right: edgeRightInput.value ? parseInt(edgeRightInput.value) : null,

//         compatible_categories: [], 
//         compatible_types: [], 
//         compatible_models: [], 
//         compatible_woods: Array.from(selectedWoodIds),
//         hardware_requirements: hardwareRequirements,
//     };
    
//     try {
//         if (partId) {
//             await updateModularPart(partId, partData);
//         } else {
//             await createModularPart(partData);
//         }
//         partFormContainer.classList.add("d-none"); // Hide the form after submission
//         await loadPartsForProduct(currentProductId);
//     } catch (error) {
//         alert("Failed to save part. " + error.message);
//         console.error("Part save error:", error);
//     }
// });

// partsList.addEventListener("click", async (e) => {
//     const partItem = e.target.closest(".card");
//     if (!partItem) return;

//     const partId = partItem.dataset.partId;

//     if (e.target.classList.contains("edit-part-btn")) {
//         try {
//             const part = await fetchModularParts(null, partId);
            
//             partIdInput.value = part.id;
//             partProductIdInput.value = part.modular_product;
//             partNameInput.value = part.name;
//             partLengthInput.value = part.part_length_equation;
//             partWidthInput.value = part.part_width_equation;
//             partQtyInput.value = part.part_quantity_equation;
//             partShapeInput.value = part.part_shape;
//             grainDirectionInput.value = part.grain_direction;
//             wastageMultiplierInput.value = part.shape_wastage_multiplier;
//             edgeCostInput.value = part.edge_band_grooving_cost;

//             partFormTitle.textContent = "Edit Part";
//             await loadPartFormLookups(new Set(part.compatible_woods));

//             edgeTopInput.value = part.part_edgematerial_top || '';
//             edgeBottomInput.value = part.part_edgematerial_bottom || '';
//             edgeLeftInput.value = part.part_edgematerial_left || '';
//             edgeRightInput.value = part.part_edgematerial_right || '';

//             hardwareRequirementsContainer.innerHTML = '';
//             if (part.hardware_requirements && part.hardware_requirements.length > 0) {
//                 noHardwareMessage.classList.add('d-none');
//                 part.hardware_requirements.forEach(req => {
//                     const reqForm = createHardwareRequirementForm(req, allHardware);
//                     hardwareRequirementsContainer.appendChild(reqForm);
//                 });
//             } else {
//                 noHardwareMessage.classList.remove('d-none');
//             }

//             partsParametersModal.hide();
//             partFormContainer.classList.remove("d-none");
//             partFormContainer.scrollIntoView({ behavior: 'smooth' });
//         } catch (error) {
//             alert("Failed to load part data for editing.");
//             console.error("Part edit load error:", error);
//         }
//     } else if (e.target.classList.contains("delete-part-btn")) {
//         if (confirm("Are you sure you want to delete this part?")) {
//             try {
//                 await deleteModularPart(partId);
//                 await loadPartsForProduct(currentProductId);
//             } catch (error) {
//                 alert("Failed to delete part.");
//                 console.error("Part delete error:", error);
//             }
//         }
//     }
// });


// // --- Parameter Management Logic ---

// const renderParametersList = (parameters) => {
//     parametersList.innerHTML = '';
//     if (parameters.length === 0) {
//         parametersList.innerHTML = "<p class='text-muted'>No parameters configured yet.</p>";
//         return;
//     }
//     parameters.forEach(param => {
//         const paramItemHtml = `
//             <div class="card mb-2" data-parameter-id="${param.id}">
//                 <div class="card-body d-flex justify-content-between align-items-center">
//                     <div>
//                         <h6 class="mb-0">${param.name} (${param.abbreviation})</h6>
//                         <small class="text-muted">Value: ${param.value}</small>
//                     </div>
//                     <div>
//                         <button class="btn btn-sm btn-info edit-parameter-btn me-2">Edit</button>
//                         <button class="btn btn-sm btn-danger delete-parameter-btn">Delete</button>
//                     </div>
//                 </div>
//             </div>
//         `;
//         parametersList.insertAdjacentHTML('beforeend', paramItemHtml);
//     });
// };

// const loadParametersForProduct = async (productId) => {
//     try {
//         const data = await fetchModularParameters(productId);
//         const parameters = data.results;
//         renderParametersList(parameters);
//     } catch (error) {
//         parametersList.innerHTML = "<p class='text-danger'>Failed to load parameters.</p>";
//         console.error(error);
//     }
// };

// addParameterBtn.addEventListener("click", () => {
//     parameterForm.reset();
//     parameterIdInput.value = "";
//     parameterProductIdInput.value = currentProductId;
//     parameterFormModal.show();
// });

// parameterForm.addEventListener("submit", async (e) => {
//     e.preventDefault();
    
//     const parameterId = parameterIdInput.value;
//     const parameterData = {
//         name: parameterNameInput.value,
//         abbreviation: parameterAbbreviationInput.value,
//         value: parseFloat(parameterValueInput.value),
//         modular_product: parseInt(parameterProductIdInput.value),
//     };

//     try {
//         if (parameterId) {
//             await updateModularParameter(parameterId, parameterData);
//         } else {
//             await createModularParameter(parameterData);
//         }
//         parameterFormModal.hide();
//         await loadParametersForProduct(currentProductId);
//     } catch (error) {
//         alert("Failed to save parameter. " + error.message);
//         console.error("Parameter save error:", error);
//     }
// });

// parametersList.addEventListener("click", async (e) => {
//     const paramItem = e.target.closest(".card");
//     if (!paramItem) return;

//     const parameterId = paramItem.dataset.parameterId;

//     if (e.target.classList.contains("edit-parameter-btn")) {
//         try {
//             const parameter = await fetchModularParameters(null, parameterId);
//             parameterIdInput.value = parameter.id;
//             parameterProductIdInput.value = parameter.modular_product;
//             parameterNameInput.value = parameter.name;
//             parameterAbbreviationInput.value = parameter.abbreviation;
//             parameterValueInput.value = parameter.value;
//             parameterFormModal.show();
//         } catch (error) {
//             alert("Failed to load parameter data for editing.");
//             console.error("Parameter edit load error:", error);
//         }
//     } else if (e.target.classList.contains("delete-parameter-btn")) {
//         if (confirm("Are you sure you want to delete this parameter?")) {
//             try {
//                 await deleteModularParameter(parameterId);
//                 await loadParametersForProduct(currentProductId);
//             } catch (error) {
//                 alert("Failed to delete parameter.");
//                 console.error("Parameter delete error:", error);
//             }
//         }
//     }
// });

// static/js/modular_dom.js

import { 
    fetchModularProducts, createModularProduct, updateModularProduct, deleteModularProduct, fetchModularProductDetail,
    fetchModularParts, createModularPart, updateModularPart, deleteModularPart,
    fetchModularParameters, createModularParameter, updateModularParameter, deleteModularParameter,
    fetchWoodMaterials, fetchEdgeBandMaterials, fetchAllHardware,
    fetchAllCategories, fetchAllCategoryTypes, fetchAllCategoryModels,
    validateModularProductDimensions // Added this for potential future validation UI
} from './modular_api.js';

// --- Global DOM Elements ---
const loadingDiv = document.getElementById("loading");
const errorDiv = document.getElementById("error");
const productCardsContainer = document.getElementById("productCardsContainer");
const createProductBtn = document.getElementById("createProductBtn");

// Product Modal Elements
const productModal = new bootstrap.Modal(document.getElementById("productModal"));
const productForm = document.getElementById("productForm");
const productIdInput = document.getElementById("productId");
const productNameInput = document.getElementById("productName");
const productDescriptionInput = document.getElementById("productDescription");
const productValidationExpressionInput = document.getElementById("productValidationExpression");
const productIsStandardInput = document.getElementById("productIsStandard");
const productIsActiveInput = document.getElementById("productIsActive");

// Parts/Parameters Modal Elements
const partsParametersModal = new bootstrap.Modal(document.getElementById("partsParametersModal"));
const modalProductName = document.getElementById("modalProductName");
const partsList = document.getElementById("partsList");
const addPartBtn = document.getElementById("addPartBtn");
const parametersList = document.getElementById("parametersList");
const addParameterBtn = document.getElementById("addParameterBtn");

// Part Form Container (Now on the main page)
const partFormContainer = document.getElementById("partFormContainer");
const partForm = document.getElementById("partForm");
const partFormTitle = document.getElementById("partFormTitle");
const closePartFormBtn = document.getElementById("closePartFormBtn");
const cancelPartFormBtn = document.getElementById("cancelPartFormBtn");
const partIdInput = document.getElementById("partId");
const partProductIdInput = document.getElementById("partProductId");
const partNameInput = document.getElementById("partName"); 
const partLengthInput = document.getElementById("partLength");
const partWidthInput = document.getElementById("partWidth");
const partQtyInput = document.getElementById("partQty");
const partShapeInput = document.getElementById("partShape");
const grainDirectionInput = document.getElementById("grainDirection");
const wastageMultiplierInput = document.getElementById("wastageMultiplier");
const edgeTopInput = document.getElementById("edgeTop");
const edgeBottomInput = document.getElementById("edgeBottom");
const edgeLeftInput = document.getElementById("edgeLeft");
const edgeRightInput = document.getElementById("edgeRight");
const edgeCostInput = document.getElementById("edgeCost");

// New Material Tree View Containers
const materialTreeContainer = document.getElementById("materialTree");
const compatibleWoodsListContainer = document.getElementById("compatibleWoodsList").querySelector('ul');

// Hardware requirements dynamic section
const hardwareRequirementsContainer = document.getElementById("hardwareRequirementsContainer");
const noHardwareMessage = document.getElementById("noHardwareMessage");
const addHardwareRequirementBtn = document.getElementById("addHardwareRequirementBtn");

// Parameter Form Modal Elements
const parameterFormModal = new bootstrap.Modal(document.getElementById("parameterFormModal"));
const parameterForm = document.getElementById("parameterForm");
const parameterIdInput = document.getElementById("parameterId");
const parameterProductIdInput = document.getElementById("parameterProductId");
const parameterNameInput = document.getElementById("parameterName");
const parameterAbbreviationInput = document.getElementById("parameterAbbreviation");
const parameterValueInput = document.getElementById("parameterValue");

let partFormSubmitMode = 'save'; // default mode
document.querySelectorAll('#partForm button[type="submit"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
        partFormSubmitMode = e.target.dataset.action || 'save';  // "save" or "save-add"
    });
});
// --- Global State ---
let currentProductId = null;
let allWoodMaterials = [];
let allEdgeBandMaterials = [];
let allCategories = [];
let allTypes = [];
let allModels = [];
let allHardware = [];

// To store the current selections for the tree view
let selectedWoodIds = new Set();


// --- Helper Functions ---

const populateSelect = (selectElement, items, selectedIds = []) => {
    selectElement.innerHTML = '';
    
    if (!selectElement.multiple) {
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = '--- Select ---';
        selectElement.appendChild(defaultOption);
    }

    items.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = item.name;
        if (selectedIds.includes(item.id)) {
            option.selected = true;
        }
        selectElement.appendChild(option);
    });
};

const createHardwareRequirementForm = (requirement = {}, allHardware) => {
    const div = document.createElement('div');
    div.classList.add('hardware-requirement-item', 'mb-3', 'p-3', 'border', 'rounded');
    div.innerHTML = `
        <input type="hidden" class="hardware-requirement-id" value="${requirement.id || ''}">
        <div class="row g-2 align-items-end">
            <div class="col-md-6">
                <label class="form-label">Hardware</label>
                <select class="form-select hardware-select" required></select>
            </div>
            <div class="col-md-5">
                <label class="form-label">Quantity Equation</label>
                <input type="text" class="form-control hardware-equation" value="${requirement.equation || ''}" placeholder="e.g., L / 100">
            </div>
            <div class="col-md-1">
                <button type="button" class="btn btn-danger btn-sm remove-hardware-requirement-btn">X</button>
            </div>
        </div>
    `;
    
    const hardwareSelect = div.querySelector('.hardware-select');
    populateSelect(hardwareSelect, allHardware, requirement.hardware ? [requirement.hardware] : []);
    
    if (requirement.hardware) {
        hardwareSelect.value = requirement.hardware;
    }

    div.querySelector('.remove-hardware-requirement-btn').addEventListener('click', () => {
        div.remove();
        if (hardwareRequirementsContainer.children.length === 1) { // Only the 'noHardwareMessage' remains
            noHardwareMessage.classList.remove('d-none');
        }
    });

    return div;
};

// --- Main Product CRUD ---

const renderProductCard = (product) => {
    const cardHtml = `
        <div class="col" data-product-id="${product.id}">
            <div class="card h-100">
                <div class="card-body">
                    <h5 class="card-title">${product.name}</h5>
                    <p class="card-text">
                        Description: ${product.description || 'N/A'}<br>
                        Validation: ${product.product_validation_expression || 'None'}
                    </p>
                </div>
                <div class="card-footer d-flex justify-content-between">
                    <button class="btn btn-sm btn-info edit-btn">Edit</button>
                    <button class="btn btn-sm btn-primary manage-parts-btn">Manage Parts & Parameters</button>
                    <button class="btn btn-sm btn-danger delete-btn">Delete</button>
                </div>
            </div>
        </div>
    `;
    productCardsContainer.insertAdjacentHTML('beforeend', cardHtml);
};

const loadProducts = async () => {
    loadingDiv.classList.remove("d-none");
    errorDiv.classList.add("d-none");
    productCardsContainer.innerHTML = '';
    
    try {
        const data = await fetchModularProducts();
        const products = data.results; // Assuming API returns { results: [], count: ... }
        
        if (products.length === 0) {
            productCardsContainer.innerHTML = "<p class='text-muted'>No modular products found.</p>";
        } else {
            products.forEach(renderProductCard);
        }
    } catch (error) {
        errorDiv.classList.remove("d-none"); // Corrected typo here
        errorDiv.textContent = `Failed to load products: ${error.message || 'Unknown error'}. Please try again.`;
        console.error(error);
    } finally {
        loadingDiv.classList.add("d-none");
    }
};

document.addEventListener("DOMContentLoaded", loadProducts);

createProductBtn.addEventListener("click", () => {
    productForm.reset();
    productIdInput.value = "";
    productModal.show();
});

productForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const productId = productIdInput.value;
    const productData = {
        name: productNameInput.value,
        description: productDescriptionInput.value,
        product_validation_expression: productValidationExpressionInput.value,
        is_standard: productIsStandardInput.checked,
        is_active: productIsActiveInput.checked,
    };
    
    try {
        if (productId) {
            await updateModularProduct(productId, productData);
        } else {
            await createModularProduct(productData);
        }
        productModal.hide();
        await loadProducts();
    } catch (error) {
        alert(`Failed to save product: ${error.message || 'Unknown error'}`);
        console.error("Product save error:", error);
    }
});

productCardsContainer.addEventListener("click", async (e) => {
    const card = e.target.closest("[data-product-id]");
    if (!card) return;

    const productId = card.dataset.productId;
    
    if (e.target.classList.contains("edit-btn")) {
        try {
            const product = await fetchModularProductDetail(productId); // Using specific fetch
            productIdInput.value = product.id;
            productNameInput.value = product.name;
            productDescriptionInput.value = product.description;
            productValidationExpressionInput.value = product.product_validation_expression;
            productIsStandardInput.checked = product.is_standard;
            productIsActiveInput.checked = product.is_active;
            productModal.show();
        } catch (error) {
            alert(`Failed to load product data for editing: ${error.message || 'Unknown error'}`);
            console.error("Product edit load error:", error);
        }
    } else if (e.target.classList.contains("delete-btn")) {
        if (confirm("Are you sure you want to delete this product?")) {
            try {
                await deleteModularProduct(productId);
                await loadProducts();
            } catch (error) {
                alert(`Failed to delete product: ${error.message || 'Unknown error'}`);
                console.error("Product delete error:", error);
            }
        }
    } else if (e.target.classList.contains("manage-parts-btn")) {
        currentProductId = productId;
        const productName = card.querySelector(".card-title").textContent;
        modalProductName.textContent = productName;
        
        await loadPartsForProduct(productId);
        await loadParametersForProduct(productId);
        partsParametersModal.show();
    }
});


// --- Part Management Logic ---

const renderPartsList = (parts) => {
    partsList.innerHTML = '';
    if (parts.length === 0) {
        partsList.innerHTML = "<p class='text-muted'>No parts configured yet.</p>";
        return;
    }
    
    parts.forEach(part => {
        const partItemHtml = `
            <div class="card mb-2" data-part-id="${part.id}">
                <div class="card-body d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-0">${part.name}</h6>
                        <small class="text-muted">L: ${part.part_length_equation || 'N/A'} | W: ${part.part_width_equation || 'N/A'} | Qty: ${part.part_quantity_equation || 'N/A'}</small>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-info edit-part-btn me-2">Edit</button>
                        <button class="btn btn-sm btn-danger delete-part-btn">Delete</button>
                    </div>
                </div>
            </div>
        `;
        partsList.insertAdjacentHTML('beforeend', partItemHtml);
    });
};

const loadPartsForProduct = async (productId) => {
    // --- ADDED CONSOLE LOGS HERE ---
    console.log('loadPartsForProduct: function called.');
    console.log('loadPartsForProduct: Received productId:', productId);
    console.log('loadPartsForProduct: Type of productId:', typeof productId);
    // --- END CONSOLE LOGS ---

    try {
        const data = await fetchModularParts(productId);
        const parts = data.results; // Assuming API returns { results: [], count: ... }
        renderPartsList(parts);
    } catch (error) {
        partsList.innerHTML = `<p class='text-danger'>Failed to load parts: ${error.message || 'Unknown error'}.</p>`;
        console.error('Error in loadPartsForProduct:', error); // More specific error log
    }
};


const getWoodIdsForHierarchy = (type, id) => {
    const woodIds = new Set();
    const parsedId = parseInt(id);

    if (type === 'wood') {
        woodIds.add(parsedId);
    } else if (type === 'model') {
        // CORRECTED: w.category_model -> w.material_model
        allWoodMaterials.filter(w => w.material_model && w.material_model.id === parsedId).forEach(w => woodIds.add(w.id));
    } else if (type === 'type') {
        // CORRECTED: w.category_type -> w.material_type, and !w.category_model -> !w.material_model
        allWoodMaterials.filter(w => w.material_type && w.material_type.id === parsedId && !w.material_model).forEach(w => woodIds.add(w.id));
        
        // CORRECTED: m.category_type -> m.model_category
        const modelsInType = allModels.filter(m => m.model_category && m.model_category.id === parsedId);
        modelsInType.forEach(model => {
            // CORRECTED: w.category_model -> w.material_model
            allWoodMaterials.filter(w => w.material_model && w.material_model.id === model.id).forEach(w => woodIds.add(w.id));
        });
    } else if (type === 'category') {
        // CORRECTED: w.category -> w.material_grp, and !w.category_type -> !w.material_type
        allWoodMaterials.filter(w => w.material_grp && w.material_grp.id === parsedId && !w.material_type).forEach(w => woodIds.add(w.id));
        
        const typesInCategory = allTypes.filter(t => t.category && t.category.id === parsedId);
        typesInCategory.forEach(type => {
            // CORRECTED: w.category_type -> w.material_type, and !w.category_model -> !w.material_model
            allWoodMaterials.filter(w => w.material_type && w.material_type.id === type.id && !w.material_model).forEach(w => woodIds.add(w.id));
            
            // CORRECTED: m.category_type -> m.model_category
            const modelsInType = allModels.filter(m => m.model_category && m.model_category.id === type.id);
            modelsInType.forEach(model => {
                // CORRECTED: w.category_model -> w.material_model
                allWoodMaterials.filter(w => w.material_model && w.material_model.id === model.id).forEach(w => woodIds.add(w.id));
            });
        });
    }
    return woodIds;
};

// --- New Tree View Material Selection Logic ---

const updateSelectedWoodsList = () => {
    compatibleWoodsListContainer.innerHTML = '';
    if (selectedWoodIds.size === 0) {
        compatibleWoodsListContainer.innerHTML = "<li class='text-muted'>No woods selected.</li>";
        return;
    }

    const woodsToDisplay = Array.from(selectedWoodIds).map(id => allWoodMaterials.find(w => w.id === id)).filter(Boolean);
    woodsToDisplay.sort((a,b) => a.name.localeCompare(b.name));
    
    woodsToDisplay.forEach(wood => {
        const li = document.createElement('li');
        li.textContent = wood.name;
        li.classList.add('py-1');
        compatibleWoodsListContainer.appendChild(li);
    });
};

const handleCheckboxChange = (event) => {
    const checkbox = event.target;
    const parentLi = checkbox.closest('li');
    const type = parentLi.dataset.type;
    const id = parentLi.dataset.id;
    const isChecked = checkbox.checked;

    const woodsToToggle = getWoodIdsForHierarchy(type, id);

    woodsToToggle.forEach(woodId => {
        if (isChecked) {
            selectedWoodIds.add(woodId);
        } else {
            selectedWoodIds.delete(woodId);
        }
    });

    // Also update children checkboxes based on parent's state
    const childCheckboxes = parentLi.querySelectorAll('ul input[type="checkbox"]');
    childCheckboxes.forEach(childCheckbox => {
        childCheckbox.checked = isChecked;
    });
    
    updateSelectedWoodsList();
};

const handleTreeItemClick = (event) => {
    const target = event.target;
    const parentLi = target.closest('li');

    if (target.classList.contains('expand-toggle')) {
        const nestedList = parentLi.querySelector('ul');
        if (nestedList) {
            nestedList.classList.toggle('d-none');
            target.textContent = nestedList.classList.contains('d-none') ? '+' : '-';
        }
    }
};

const renderMaterialTree = (initialSelectionIds = new Set()) => {
    selectedWoodIds = initialSelectionIds;
    materialTreeContainer.innerHTML = '';
    const mainUl = document.createElement('ul');
    mainUl.classList.add('list-unstyled', 'm-0');

    allCategories.forEach(category => {
        const categoryLi = document.createElement('li');
        categoryLi.classList.add('py-1', 'ps-1');
        categoryLi.dataset.type = 'category'; // Add dataset for consistency
        categoryLi.dataset.id = category.id; // Add dataset for consistency
        
        const typesInCat = allTypes.filter(t => t.category && t.category.id === category.id);
        // CORRECTED: w.category -> w.material_grp
        const woodsInCat = allWoodMaterials.filter(w => w.material_grp && w.material_grp.id === category.id && !w.material_type); 
        const hasChildren = typesInCat.length > 0 || woodsInCat.length > 0;
        const toggleSpan = hasChildren ? `<span class="expand-toggle me-2 fw-bold cursor-pointer">+</span>` : `<span class="me-2 invisible">-</span>`;
        // Check if ALL woods under this category are selected
        const allCategoryWoods = getWoodIdsForHierarchy('category', category.id);
        const categoryChecked = allCategoryWoods.size > 0 && [...allCategoryWoods].every(id => selectedWoodIds.has(id));
        
        categoryLi.innerHTML = `
            ${toggleSpan}
            <input type="checkbox" id="cat-${category.id}" class="form-check-input me-1" data-type="category" data-id="${category.id}" ${categoryChecked ? 'checked' : ''}>
            <label for="cat-${category.id}" class="form-check-label">${category.name}</label>
        `;

        if (hasChildren) {
            const nestedUl = document.createElement('ul');
            nestedUl.classList.add('list-unstyled', 'ps-4', 'm-0', 'd-none');
            
            woodsInCat.forEach(wood => {
                const woodLi = document.createElement('li');
                woodLi.classList.add('py-1', 'ps-1');
                woodLi.dataset.type = 'wood';
                woodLi.dataset.id = wood.id;
                woodLi.innerHTML = `<input type="checkbox" id="wood-${wood.id}" class="form-check-input me-1" data-type="wood" data-id="${wood.id}" ${selectedWoodIds.has(wood.id) ? 'checked' : ''}><label for="wood-${wood.id}" class="form-check-label">${wood.name}</label>`;
                nestedUl.appendChild(woodLi);
            });

            typesInCat.forEach(type => {
                const typeLi = document.createElement('li');
                typeLi.classList.add('py-1', 'ps-1');
                typeLi.dataset.type = 'type'; // Add dataset
                typeLi.dataset.id = type.id; // Add dataset
                
                // CORRECTED: m.category_type -> m.model_category
                const modelsInType = allModels.filter(m => m.model_category && m.model_category.id === type.id);
                // CORRECTED: w.category_type -> w.material_type, and !w.category_model -> !w.material_model
                const woodsInType = allWoodMaterials.filter(w => w.material_type && w.material_type.id === type.id && !w.material_model);
                const hasTypeChildren = modelsInType.length > 0 || woodsInType.length > 0;
                const typeToggle = hasTypeChildren ? `<span class="expand-toggle me-2 fw-bold cursor-pointer">+</span>` : `<span class="me-2 invisible">-</span>`;
                // Check if ALL woods under this type are selected
                const allTypeWoods = getWoodIdsForHierarchy('type', type.id);
                const typeChecked = allTypeWoods.size > 0 && [...allTypeWoods].every(id => selectedWoodIds.has(id));

                typeLi.innerHTML = `
                    ${typeToggle}
                    <input type="checkbox" id="type-${type.id}" class="form-check-input me-1" data-type="type" data-id="${type.id}" ${typeChecked ? 'checked' : ''}>
                    <label for="type-${type.id}" class="form-check-label">${type.name}</label>
                `;

                if (hasTypeChildren) {
                    const nestedTypeUl = document.createElement('ul');
                    nestedTypeUl.classList.add('list-unstyled', 'ps-4', 'm-0', 'd-none');

                    woodsInType.forEach(wood => {
                        const woodLi = document.createElement('li');
                        woodLi.classList.add('py-1', 'ps-1');
                        woodLi.dataset.type = 'wood';
                        woodLi.dataset.id = wood.id;
                        woodLi.innerHTML = `<input type="checkbox" id="wood-${wood.id}" class="form-check-input me-1" data-type="wood" data-id="${wood.id}" ${selectedWoodIds.has(wood.id) ? 'checked' : ''}><label for="wood-${wood.id}" class="form-check-label">${wood.name}</label>`;
                        nestedTypeUl.appendChild(woodLi);
                    });

                    modelsInType.forEach(model => {
                        const modelLi = document.createElement('li');
                        modelLi.classList.add('py-1', 'ps-1');
                        modelLi.dataset.type = 'model'; // Add dataset
                        modelLi.dataset.id = model.id; // Add dataset
                        
                        // CORRECTED: w.category_model -> w.material_model
                        const woodsInModel = allWoodMaterials.filter(w => w.material_model && w.material_model.id === model.id);
                        const hasModelChildren = woodsInModel.length > 0;
                        const modelToggle = hasModelChildren ? `<span class="expand-toggle me-2 fw-bold cursor-pointer">+</span>` : `<span class="me-2 invisible">-</span>`;
                        // Check if ALL woods under this model are selected
                        const allModelWoods = getWoodIdsForHierarchy('model', model.id);
                        const modelChecked = allModelWoods.size > 0 && [...allModelWoods].every(id => selectedWoodIds.has(id));

                        modelLi.innerHTML = `
                            ${modelToggle}
                            <input type="checkbox" id="model-${model.id}" class="form-check-input me-1" data-type="model" data-id="${model.id}" ${modelChecked ? 'checked' : ''}>
                            <label for="model-${model.id}" class="form-check-label">${model.name}</label>
                        `;

                        if (hasModelChildren) {
                            const nestedModelUl = document.createElement('ul');
                            nestedModelUl.classList.add('list-unstyled', 'ps-4', 'm-0', 'd-none');
                            woodsInModel.forEach(wood => {
                                const woodLi = document.createElement('li');
                                woodLi.classList.add('py-1', 'ps-1');
                                woodLi.dataset.type = 'wood';
                                woodLi.dataset.id = wood.id;
                                woodLi.innerHTML = `<input type="checkbox" id="wood-${wood.id}" class="form-check-input me-1" data-type="wood" data-id="${wood.id}" ${selectedWoodIds.has(wood.id) ? 'checked' : ''}><label for="wood-${wood.id}" class="form-check-label">${wood.name}</label>`;
                                nestedModelUl.appendChild(woodLi);
                            });
                            modelLi.appendChild(nestedModelUl);
                        }
                        nestedTypeUl.appendChild(modelLi);
                    });
                    typeLi.appendChild(nestedTypeUl);
                }
                nestedUl.appendChild(typeLi);
            });
            categoryLi.appendChild(nestedUl);
        }
        mainUl.appendChild(categoryLi);
    });

    materialTreeContainer.appendChild(mainUl);

    materialTreeContainer.addEventListener('change', handleCheckboxChange);
    materialTreeContainer.addEventListener('click', handleTreeItemClick);
    
    updateSelectedWoodsList();
};

const loadPartFormLookups = async (initialSelectionIds = new Set()) => {
    try {
        const woodData = await fetchWoodMaterials();
        allWoodMaterials = woodData.results || woodData; // Adjust for pagination vs direct array

        const edgeBandData = await fetchEdgeBandMaterials();
        allEdgeBandMaterials = edgeBandData.results || edgeBandData;

        const categoriesData = await fetchAllCategories();
        allCategories = categoriesData.results || categoriesData;
        
        const typesData = await fetchAllCategoryTypes();
        allTypes = typesData.results || typesData;
        
        const modelsData = await fetchAllCategoryModels();
        allModels = modelsData.results || modelsData;
        
        const hardwareData = await fetchAllHardware();
        allHardware = (hardwareData.results || hardwareData).map(hw => ({
            ...hw,
            name: hw.h_name // Map h_name to name for populateSelect
        }));
        
        populateSelect(edgeTopInput, allEdgeBandMaterials);
        populateSelect(edgeBottomInput, allEdgeBandMaterials);
        populateSelect(edgeLeftInput, allEdgeBandMaterials);
        populateSelect(edgeRightInput, allEdgeBandMaterials);

        renderMaterialTree(initialSelectionIds);

    } catch (error) {
        console.error("Failed to load part form lookup data:", error);
        alert(`Failed to load necessary data for part form: ${error.message || 'Unknown error'}. Check console for details.`);
    }
};

addPartBtn.addEventListener("click", async () => {
    partForm.reset();
    partIdInput.value = "";
    partProductIdInput.value = currentProductId;
    partFormTitle.textContent = "Add New Part";
    
    selectedWoodIds.clear(); // Clear previous selections
    hardwareRequirementsContainer.innerHTML = ''; // Clear existing hardware forms
    noHardwareMessage.classList.remove('d-none'); // Show message initially
    
    await loadPartFormLookups();
    partFormContainer.classList.remove("d-none");
    partsParametersModal.hide(); // Hide the parts/parameters modal
    partFormContainer.scrollIntoView({ behavior: 'smooth' });
});

closePartFormBtn.addEventListener('click', () => {
    partFormContainer.classList.add("d-none");
});

cancelPartFormBtn.addEventListener('click', () => {
    partFormContainer.classList.add("d-none");
});

addHardwareRequirementBtn.addEventListener('click', () => {
    noHardwareMessage.classList.add('d-none'); // Hide "no hardware" message
    const newHardwareForm = createHardwareRequirementForm({}, allHardware);
    hardwareRequirementsContainer.appendChild(newHardwareForm);
});


partForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const partId = partIdInput.value;

    const hardwareRequirements = [];
    hardwareRequirementsContainer.querySelectorAll('.hardware-requirement-item').forEach(item => {
        const reqId = item.querySelector('.hardware-requirement-id').value;
        const hardwareId = item.querySelector('.hardware-select').value;
        const equation = item.querySelector('.hardware-equation').value;

        // Only include valid requirements
        if (hardwareId && equation) {
            hardwareRequirements.push({
                id: reqId ? parseInt(reqId) : undefined, // Convert to int if exists
                hardware: parseInt(hardwareId),
                equation: equation
            });
        }
    });

    const partData = {
        name: partNameInput.value,
        modular_product: parseInt(partProductIdInput.value),
        part_length_equation: partLengthInput.value,
        part_width_equation: partWidthInput.value,
        part_qty_equation: partQtyInput.value,
        part_shape: partShapeInput.value,
        grain_direction: grainDirectionInput.value,
        shape_wastage_multiplier: parseFloat(wastageMultiplierInput.value) || 0, // Default to 0 if empty
        edge_band_grooving_cost: parseFloat(edgeCostInput.value) || 0, // Default to 0 if empty
        
        part_edgematerial_top: edgeTopInput.value ? parseInt(edgeTopInput.value) : null,
        part_edgematerial_bottom: edgeBottomInput.value ? parseInt(edgeBottomInput.value) : null,
        part_edgematerial_left: edgeLeftInput.value ? parseInt(edgeLeftInput.value) : null,
        part_edgematerial_right: edgeRightInput.value ? parseInt(edgeRightInput.value) : null,

        // These are determined by the tree view, not direct selection.
        // The backend `compatible_woods` field in Part1 takes a list of IDs directly.
        compatible_categories: [], 
        compatible_types: [], 
        compatible_models: [], 
        compatible_woods: Array.from(selectedWoodIds), // Send selected wood IDs directly
        hardware_requirements: hardwareRequirements,
    };
    
    try {
        if (partId) {
            await updateModularPart(partId, partData);
        } else {
            await createModularPart(partData);
        }
        await loadPartsForProduct(currentProductId);

        if (partFormSubmitMode === 'save-add') {
            // Reset form for a new entry
            partForm.reset();
            partIdInput.value = '';  // clear ID for new create
            await loadPartFormLookups();  // clear tree + dropdowns
            hardwareRequirementsContainer.innerHTML = '';
            noHardwareMessage.classList.remove('d-none');
            partNameInput.focus(); // focus on name field
        } else {
            // Normal save: hide form and show list
            partFormContainer.classList.add("d-none");
            partsParametersModal.show();
        } // Show parts/parameters modal again
    } catch (error) {
        alert(`Failed to save part: ${error.message || 'Unknown error'}`);
        console.error("Part save error:", error);
    }
});

partsList.addEventListener("click", async (e) => {
    const partItem = e.target.closest(".card");
    if (!partItem) return;

    const partId = partItem.dataset.partId;

    if (e.target.classList.contains("edit-part-btn")) {
        try {
            const part = await fetchModularParts(null, partId); // Fetch single part by ID
            
            partIdInput.value = part.id;
            partProductIdInput.value = part.modular_product;
            partNameInput.value = part.name;
            partLengthInput.value = part.part_length_equation;
            partWidthInput.value = part.part_width_equation;
            partQtyInput.value = part.part_quantity_equation;
            partShapeInput.value = part.part_shape;
            grainDirectionInput.value = part.grain_direction;
            wastageMultiplierInput.value = part.shape_wastage_multiplier;
            edgeCostInput.value = part.edge_band_grooving_cost;

            partFormTitle.textContent = "Edit Part";
            // Populate material tree with existing selections
            await loadPartFormLookups(new Set(part.compatible_woods)); 

            // Populate edge material dropdowns
            edgeTopInput.value = part.part_edgematerial_top || '';
            edgeBottomInput.value = part.part_edgematerial_bottom || '';
            edgeLeftInput.value = part.part_edgematerial_left || '';
            edgeRightInput.value = part.part_edgematerial_right || '';

            // Populate hardware requirements
            hardwareRequirementsContainer.innerHTML = ''; // Clear existing forms
            if (part.hardware_requirements && part.hardware_requirements.length > 0) {
                noHardwareMessage.classList.add('d-none');
                part.hardware_requirements.forEach(req => {
                    const reqForm = createHardwareRequirementForm(req, allHardware);
                    hardwareRequirementsContainer.appendChild(reqForm);
                });
            } else {
                noHardwareMessage.classList.remove('d-none');
            }

            partsParametersModal.hide(); // Hide the parts/parameters modal
            partFormContainer.classList.remove("d-none"); // Show the part form
            partFormContainer.scrollIntoView({ behavior: 'smooth' });
        } catch (error) {
            alert(`Failed to load part data for editing: ${error.message || 'Unknown error'}`);
            console.error("Part edit load error:", error);
        }
    } else if (e.target.classList.contains("delete-part-btn")) {
        if (confirm("Are you sure you want to delete this part?")) {
            try {
                await deleteModularPart(partId);
                await loadPartsForProduct(currentProductId);
            } catch (error) {
                alert(`Failed to delete part: ${error.message || 'Unknown error'}`);
                console.error("Part delete error:", error);
            }
        }
    }
});


// --- Parameter Management Logic ---

const renderParametersList = (parameters) => {
    parametersList.innerHTML = '';
    if (parameters.length === 0) {
        parametersList.innerHTML = "<p class='text-muted'>No parameters configured yet.</p>";
        return;
    }
    parameters.forEach(param => {
        const paramItemHtml = `
            <div class="card mb-2" data-parameter-id="${param.id}">
                <div class="card-body d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-0">${param.name} (${param.abbreviation})</h6>
                        <small class="text-muted">Value: ${param.value}</small>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-info edit-parameter-btn me-2">Edit</button>
                        <button class="btn btn-sm btn-danger delete-parameter-btn">Delete</button>
                    </div>
                </div>
            </div>
        `;
        parametersList.insertAdjacentHTML('beforeend', paramItemHtml);
    });
};

const loadParametersForProduct = async (productId) => {
    try {
        const data = await fetchModularParameters(productId);
        const parameters = data.results; // Assuming API returns { results: [], count: ... }
        renderParametersList(parameters);
    } catch (error) {
        parametersList.innerHTML = `<p class='text-danger'>Failed to load parameters: ${error.message || 'Unknown error'}.</p>`;
        console.error(error);
    }
};

addParameterBtn.addEventListener("click", () => {
    parameterForm.reset();
    parameterIdInput.value = "";
    parameterProductIdInput.value = currentProductId;
    parameterFormModal.show();
});

parameterForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const parameterId = parameterIdInput.value;
    const parameterData = {
        name: parameterNameInput.value,
        abbreviation: parameterAbbreviationInput.value,
        value: parameterValueInput.value,
        modular_product: parseInt(parameterProductIdInput.value),
    };
    
    try {
        if (parameterId) {
            await updateModularParameter(parameterId, parameterData);
        } else {
            await createModularParameter(parameterData);
        }
        parameterFormModal.hide();
        await loadParametersForProduct(currentProductId);
    } catch (error) {
        alert(`Failed to save parameter: ${error.message || 'Unknown error'}`);
        console.error("Parameter save error:", error);
    }
});

parametersList.addEventListener("click", async (e) => {
    const parameterItem = e.target.closest(".card");
    if (!parameterItem) return;

    const parameterId = parameterItem.dataset.parameterId;

    if (e.target.classList.contains("edit-parameter-btn")) {
        try {
            const parameter = await fetchModularParameters(null, parameterId); // Fetch single parameter
            
            parameterIdInput.value = parameter.id;
            parameterProductIdInput.value = parameter.modular_product;
            parameterNameInput.value = parameter.name;
            parameterAbbreviationInput.value = parameter.abbreviation;
            parameterValueInput.value = parameter.value;
            parameterFormModal.show();
        } catch (error) {
            alert(`Failed to load parameter data for editing: ${error.message || 'Unknown error'}`);
            console.error("Parameter edit load error:", error);
        }
    } else if (e.target.classList.contains("delete-parameter-btn")) {
        if (confirm("Are you sure you want to delete this parameter?")) {
            try {
                await deleteModularParameter(parameterId);
                await loadParametersForProduct(currentProductId);
            } catch (error) {
                alert(`Failed to delete parameter: ${error.message || 'Unknown error'}`);
                console.error("Parameter delete error:", error);
            }
        }
    }
});
import * as api from './modular_api.js'; 

// Function to handle the login form submission within the modal
export function setupLoginModalHandler() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // Prevent default form submission

            const username = document.getElementById('usernameInput').value;
            const password = document.getElementById('passwordInput').value;
            const loginErrorAlert = document.getElementById('loginErrorAlert');

            // --- IMPORTANT CHANGE: Use URLSearchParams for form-encoded data ---
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);
            // --- END IMPORTANT CHANGE ---

            try {
                // Adjust this URL if your customer app's URL prefix is different (e.g., '/customer/ajax-login/')
                const response = await fetch('/customer/ajax-login/', { 
                    method: 'POST',
                    headers: {
                        // REMOVE 'Content-Type': 'application/json'
                        // fetch API will automatically set 'Content-Type: application/x-www-form-urlencoded'
                        // when the body is a URLSearchParams object.
                        'X-CSRFToken': api.getCookie('csrftoken') // Keep CSRF token header
                    },
                    body: formData // Send the URLSearchParams object
                });

                if (!response.ok) {
                    const errorData = await response.json(); // Still expect JSON error responses from backend
                    let errorMessage = 'Login failed. Please try again.';
                    if (errorData.message) { // Your backend sends 'message'
                        errorMessage = errorData.message;
                    } else if (errorData.detail) { // DRF style 'detail'
                        errorMessage = errorData.detail;
                    }
                    loginErrorAlert.textContent = errorMessage;
                    loginErrorAlert.classList.remove('d-none');
                    return; // Stop here if login failed
                }

                // Login successful
                const successData = await response.json();
                hideLoginModal();
                if (successData.redirect_url) {
                    window.location.href = successData.redirect_url;
                } else {
                    location.reload(); // Fallback
                }

            } catch (error) {
                console.error("Login error:", error);
                loginErrorAlert.textContent = 'An unexpected error occurred during login.';
                loginErrorAlert.classList.remove('d-none');
            }
        });
    }
}