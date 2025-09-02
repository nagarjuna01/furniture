// modular_user.js

import { fetchModularProducts } from './modular_api.js';
import { validateExpression } from './modular_utils.js';

document.addEventListener('DOMContentLoaded', async () => {
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const validationForm = document.getElementById('validationForm');
    const inputLength = document.getElementById('inputLength');
    const inputWidth = document.getElementById('inputWidth');
    const inputHeight = document.getElementById('inputHeight');
    const validationResultDiv = document.getElementById('validationResult');

    let validationExpression = null;

    // Fetch the product details to get the validation expression
    try {
        loading.classList.remove('d-none');
        // Fetch a single product by its ID if your API supports it.
        // If not, fetch all and find the correct product.
        const data = await fetchModularProducts();
        const product = data.results.find(p => p.id == window.PRODUCT_ID);
        
        if (product && product.product_validation_expression) {
            validationExpression = product.product_validation_expression;
            loading.classList.add('d-none');
        } else {
            loading.classList.add('d-none');
            error.classList.remove('d-none');
            error.textContent = 'Could not find product or validation rule.';
        }
    } catch (err) {
        loading.classList.add('d-none');
        error.classList.remove('d-none');
        console.error('Fetch error:', err);
    }
    
    // Handle form submission for validation
    validationForm.addEventListener('submit', (event) => {
        event.preventDefault();

        if (!validationExpression) {
            validationResultDiv.className = 'alert alert-warning';
            validationResultDiv.textContent = 'Validation rules are not available.';
            return;
        }

        const l = parseFloat(inputLength.value);
        const w = parseFloat(inputWidth.value);
        const h = parseFloat(inputHeight.value);

        if (isNaN(l) || isNaN(w) || isNaN(h)) {
            validationResultDiv.className = 'alert alert-warning';
            validationResultDiv.textContent = 'Please enter valid numbers for all dimensions.';
            return;
        }

        const isValid = validateExpression(validationExpression, l, w, h);

        if (isValid) {
            validationResultDiv.className = 'alert alert-success';
            validationResultDiv.textContent = 'Validation successful! The dimensions pass the rule.';
        } else {
            validationResultDiv.className = 'alert alert-danger';
            validationResultDiv.textContent = 'Validation failed. The dimensions do not pass the rule.';
        }
    });
});