// core/engine-connector.js
class QuotationEngine {
    constructor(productId, tenantId) {
        this.productId = productId;
        this.tenantId = tenantId;
        this.state = {
            product_dims: {}, // Populated from ModularProduct requirements
            parameters: {},   // Populated from ProductParameter model
            quantities: [1]
        };
    }

    // Hits the 'run' action in your modular_calcapp.txt
    async evaluate() {
        const response = await fetch(`/api/evaluate/products/${this.productId}/run/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Tenant-ID': this.tenantId // Critical for your 500-site isolation
            },
            body: JSON.stringify(this.state)
        });
        
        if (!response.ok) {
            const error = await response.json();
            this.handleValidationError(error);
            return null;
        }
        
        return await response.json(); // Returns {total_sp, total_cp, parts, hardware}
    }

    updateDimension(key, value) {
        this.state.product_dims[key] = value;
        return this.evaluate(); // Auto-trigger re-calc
    }
}