/**
 * GLOBAL ENGINE - UNIFIED FACTORY REGISTRY (Corrected & Bridged)
 */

const FactoryEngine = {
    mode: 'modular', 
    searchController: null,
    selectedProduct: null,

    init() {
        this.bindEvents();
        this.updateUIState();
        this.fetchData();
        console.log("Global Engine Factory: 4-Stage Online");
    },

    bindEvents() {
        $('.factory-btn').on('click', (e) => {
            const btn = $(e.currentTarget);
            this.mode = btn.data('mode');
            $('.factory-btn').removeClass('btn-primary').addClass('btn-outline-primary');
            btn.addClass('btn-primary').removeClass('btn-outline-primary');
            this.updateUIState();
            this.fetchData();
        });

        // Listen for all 4 stages of filtering
        $('#engine-search, #filter-cat, #filter-type, #filter-model').on('input change', () => {
            this.fetchData();
        });
    },

    updateUIState() {
    const isMod = this.mode === 'modular';
    
    // Stage 3 Toggle
    $('#model-filter-container').toggle(isMod);
    
    // Stage 4 Toggle (Optional: hide L4 dropdown if using Search instead)
    $('#layer-4-container').toggle(!isMod); 

    if (isMod) {
        $('#filter-type option:first').text("Type (L2)");
        $('#filter-model option:first').text("Model (L3)");
    } else {
        $('#filter-type option:first').text("Series (L2)");
        $('#filter-model').val(""); 
    }
    $('#lbh-configurator').addClass('d-none');
},

    async fetchData() {
        if (this.searchController) this.searchController.abort();
        this.searchController = new AbortController();

        const endpoint = this.mode === 'modular' 
            ? '/modularcalc/api/products/' 
            : '/products1/v1/products/'; 

        const params = new URLSearchParams({
            category: $('#filter-cat').val() || '',
            type: $('#filter-type').val() || '',
            model: $('#filter-model').val() || '',
            search: $('#engine-search').val() || ''
        });

        try {
            const response = await fetch(`${endpoint}?${params}`, {
                signal: this.searchController.signal
            });
            const data = await response.json();
            const items = data.results ? data.results : (Array.isArray(data) ? data : []);
            this.renderTable(items);
        } catch (err) {
            if (err.name === 'AbortError') return;
            $('#registry-body').html(`<tr><td colspan="4" class="text-center py-3 text-danger">Factory Syncing...</td></tr>`);
        }
    },

    renderTable(items) {
        const $body = $('#registry-body').empty();
        if (items.length === 0) {
            $body.append('<tr><td colspan="4" class="text-center py-4 text-muted">No DNA matches found.</td></tr>');
            return;
        }

        items.forEach(item => {
            const path = this.mode === 'modular' 
                ? `${item.category_name || 'N/A'} > ${item.type_name || 'N/A'}`
                : `${item.category_name || 'N/A'}`;

            $body.append(`
                <tr>
                    <td>
                        <div class="fw-bold text-dark">${item.name}</div>
                        <small class="text-muted">${item.sku || item.code || ''}</small>
                    </td>
                    <td><small class="text-secondary">${path}</small></td>
                    <td>
                        <span class="badge ${this.mode === 'modular' ? 'bg-info' : 'bg-success'} shadow-sm">
                            ${this.mode.toUpperCase()}
                        </span>
                    </td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-dark px-3" onclick="FactoryEngine.selectProduct('${item.id}')">Select</button>
                    </td>
                </tr>`);
        });
    },

    async selectProduct(id) {
    const endpoint = this.mode === 'modular' 
        ? `/modularcalc/api/products/${id}/` 
        : `/products1/v1/products/${id}/`;

    const res = await fetch(endpoint);
    this.selectedProduct = await res.json();
    
    // --- THE CRITICAL FIX ---
    // Explicitly tell QuoteApp which factory mode we are in 
    // BEFORE showing the panel.
    QuoteApp.currentFactory = this.mode; 
    QuoteApp.selectedItemId = id; 
    
    this.showConfigPanel(this.selectedProduct);
},
showConfigPanel(product) {
    $('#lbh-configurator').removeClass('d-none');
    $('#selected-product-title').text(`Configuring: ${product.name}`);
    const $fields = $('#dimension-fields').empty();

    // Fix: We change FactoryEngine.addToQuote() to QuoteApp.addItem() 
    // to match your unified workspace logic.

    if (this.mode === 'modular') {
        $fields.append(`
            <div class="col-md-3"><label class="small fw-bold">LENGTH</label><input type="number" id="cfg-L" class="form-control" value="1000"></div>
            <div class="col-md-3"><label class="small fw-bold">WIDTH</label><input type="number" id="cfg-W" class="form-control" value="600"></div>
            <div class="col-md-3"><label class="small fw-bold">HEIGHT</label><input type="number" id="cfg-H" class="form-control" value="750"></div>
            <div class="col-md-3 d-flex align-items-end">
                <button class="btn btn-primary w-100 fw-bold" onclick="QuoteApp.addItem()">ADD TO ZONE</button>
            </div>
        `);
    } else {
        const variants = product.variants || [];
        if (variants.length > 0) {
            let options = variants.map(v => `<option value="${v.id}">${v.length}x${v.width}x${v.height} - ${v.sku}</option>`).join('');
            $fields.append(`
                <div class="col-md-8"><label class="small fw-bold">Select Variant</label><select id="target-variant-id" class="form-select">${options}</select></div>
                <div class="col-md-4 d-flex align-items-end">
                    <button class="btn btn-success w-100 fw-bold" onclick="QuoteApp.addItem()">ADD TO ZONE</button>
                </div>
            `);
        }
    }
},

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
};

$(document).ready(() => FactoryEngine.init());