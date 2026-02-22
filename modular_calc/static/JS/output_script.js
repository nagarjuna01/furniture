function engineHandler() {
    return {
        // --- REACTIVE STATE ---
        productId: '',
        materialId: '',
        materials: [],
        loading: false,
        status: 'Ready...',
        quote: null,
        dims: { length: 1000, width: 600, height: 750 },
        customParams: '{}',

        // --- ACTIONS ---

        async init() {
            const urlParams = new URLSearchParams(window.location.search);
            const urlId = urlParams.get('product_id');
            
            this.$nextTick(async () => {
                const sidebarEl = document.getElementById('dev-product-id');
                this.productId = urlId || (sidebarEl ? sidebarEl.value : '');
                
                if (this.productId && this.productId !== "None") {
                    await this.fetchMaterials();
                } else {
                    this.status = "System Ready. Please select a model.";
                }
            });
        },

        async fetchMaterials() {
            if (!this.productId || this.productId === "None" || this.productId === "") return;
            
            this.status = "Syncing materials with Engine...";
            try {
                const res = await fetch(`/modularcalc/api/products/${this.productId}/`);
                if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
                
                const data = await res.json();
                this.materials = data.part_templates?.[0]?.material_whitelist || [];
                
                if (this.materials.length > 0) {
                    this.materialId = this.materials[0].material;
                    this.status = `${this.materials.length} Materials synchronized.`;
                } else {
                    this.materialId = '';
                    this.status = "Warning: Product has no whitelist.";
                }
            } catch (e) {
                this.status = "API Connection Error.";
            }
        },

        async runEngine() {
            const token = this.getCsrfToken();
            
            // Validate token before sending to avoid "incorrect length" errors
            if (!token || token.length < 32) {
                this.status = "CSRF Error: Security token missing in HTML.";
                alert("Security Error: Please ensure {% csrf_token %} is present in the HTML <body>.");
                return;
            }

            if (!this.productId || !this.materialId) {
                this.status = "Selection Required.";
                return;
            }

            this.loading = true;
            this.status = "Optimizing...";
            
            try {
                const response = await fetch(`/modularcalc/api/products/${this.productId}/evaluate/`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json', 
                        'X-CSRFToken': token 
                    },
                    body: JSON.stringify({
                        product_dims: {
                            product_length: this.dims.length,
                            product_width: this.dims.width,
                            product_height: this.dims.height
                        },
                        quantities: [1],
                        material_id: this.materialId,
                        custom_parameters: JSON.parse(this.customParams || '{}')
                    })
                });

                const data = await response.json();
                
                if (data.detail && data.detail.includes("CSRF")) {
                    throw new Error("CSRF Token Invalid or Expired.");
                }

                const firstKey = Object.keys(data.quotes)[0];
                this.quote = data.quotes[firstKey];
                this.status = "Success.";
            } catch (err) {
                this.status = `Error: ${err.message}`;
            } finally {
                this.loading = false;
            }
        },

        /**
         * Industrial strength CSRF retrieval
         */
        getCsrfToken() {
            // 1. Check for cookie (common in multi-tenant)
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, 10) === ('csrftoken=')) {
                        cookieValue = decodeURIComponent(cookie.substring(10));
                        break;
                    }
                }
            }
            // 2. Fallback to the {% csrf_token %} hidden input
            const inputToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            
            // 3. Final Fallback to global variable
            return cookieValue || inputToken || window.CSRF_TOKEN || "";
        }
    }
}