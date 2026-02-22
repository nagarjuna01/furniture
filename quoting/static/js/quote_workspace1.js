/**
 * Global Engine Workspace - v1.4 (Master Unified File)
 */

const QuoteApp = {
    // --- STATE ---
    quoteId: $("#quote-app").data("quote-id"),
    quote: null,
    activeSolutionId: null,
    currentFactory: 'modular', 
    selectedItemId: null,
    searchController: null,

    init() {
        this.bindEvents();
        this.loadQuote();
        this.refreshRegistry(); 
        this.startSync();
    },

    // --- DATA LOADING ---
    loadQuote() {
        const self = this;
        $.ajax({
            url: `/quoting/api/quotes/${this.quoteId}/`,
            method: "GET",
        })
        .done((data) => {
            self.quote = data;
            self.renderHeader();
            self.renderSolutions();
            
            if (!self.activeSolutionId && data.solutions?.length > 0) {
                self.selectSolution(data.solutions[0].id);
            } else if (self.activeSolutionId) {
                self.selectSolution(self.activeSolutionId);
            }
        })
        .fail(() => console.error("Engine Sync Failure."));
    },

    // --- FACTORY REGISTRY LOGIC ---
    setFactory(type) {
        this.currentFactory = type;
        $(".factory-toggle").removeClass("active btn-primary").addClass("btn-outline-primary");
        $(`#btn-fac-${type}`).addClass("active btn-primary").removeClass("btn-outline-primary");

        if (type === 'modular') {
            $("#layer-4-container").show();
            $("#lbl-layer-3").text("Product Model");
        } else {
            $("#layer-4-container").hide();
            $("#lbl-layer-3").text("Target Product");
        }
        
        this.resetFilters();
        this.refreshRegistry();
    },

    resetFilters() {
        $("#filter-cat, #filter-type, #filter-model, #search-input").val("");
        $("#config-panel").addClass("d-none").empty();
    },

    refreshRegistry() {
        if (this.searchController) this.searchController.abort();
        this.searchController = new AbortController();

        const isMod = this.currentFactory === 'modular';
        const url = isMod ? '/modularcalc/api/products/' : '/products1/v1/product-variants/';
        
        const params = {
            category: $("#filter-cat").val(),
            type: $("#filter-type").val(),
            model: isMod ? $("#filter-model").val() : null,
            search: $("#search-input").val()
        };

        $("#registry-table-body").html('<tr><td colspan="4" class="text-center py-4"><div class="spinner-border spinner-border-sm text-primary"></div></td></tr>');

        $.ajax({
            url: url,
            data: params,
            signal: this.searchController.signal,
            success: (data) => this.renderRegistryTable(data),
            error: (xhr) => { if(xhr.statusText !== 'abort') console.error("Registry Sync Failure"); }
        });
    },

    renderRegistryTable(items) {
        const $tbody = $("#registry-table-body").empty();
        const isMod = this.currentFactory === 'modular';

        if (!items.length) {
            $tbody.append('<tr><td colspan="4" class="text-center text-muted py-4">No DNA found.</td></tr>');
            return;
        }

        items.forEach(item => {
            const row = $(`
                <tr class="align-middle">
                    <td>
                        <div class="fw-bold">${item.name}</div>
                        <small class="text-muted">${item.category_name || ''} / ${item.type_name || ''}</small>
                    </td>
                    <td><span class="badge ${isMod ? 'bg-info' : 'bg-success'}">${this.currentFactory.toUpperCase()}</span></td>
                    <td><small>${isMod ? (item.productmodel_name || '-') : (item.series_name || '-')}</small></td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-primary btn-prepare" data-id="${item.id}">
                            Configure <i class="fas fa-chevron-right ms-1"></i>
                        </button>
                    </td>
                </tr>
            `);
            row.find(".btn-prepare").on("click", () => this.prepareItem(item.id));
            $tbody.append(row);
        });
    },

    prepareItem(id) {
        this.selectedItemId = id;
        const isMod = this.currentFactory === 'modular';
        const url = isMod ? `/modularcalc/api/products/${id}/` : `/products1/v1/product-variants/${id}/`;

        $("#config-panel").removeClass("d-none").html('<div class="p-4 text-center"><div class="spinner-border text-primary"></div></div>');

        $.get(url).done((product) => {
            this.renderConfigurator(product);
        });
    },

    renderConfigurator(product) {
        const isMod = this.currentFactory === 'modular';
        const $panel = $("#config-panel").empty();

        const html = `
            <div class="card border-primary shadow-sm mb-4">
                <div class="card-header bg-primary text-white">Configure: ${product.name}</div>
                <div class="card-body">
                    <div class="row g-2">
                        <div class="col-4">
                            <label class="small fw-bold">Qty</label>
                            <input type="number" id="cfg-qty" class="form-control" value="1">
                        </div>
                        ${isMod ? `
                            <div class="col-4"><label class="small fw-bold">L (mm)</label><input type="number" id="cfg-L" class="form-control" value="1000"></div>
                            <div class="col-4"><label class="small fw-bold">W (mm)</label><input type="number" id="cfg-W" class="form-control" value="600"></div>
                            <div class="col-4"><label class="small fw-bold">H (mm)</label><input type="number" id="cfg-H" class="form-control" value="750"></div>
                        ` : `
                            <div class="col-8 mt-4 text-muted small">Standard item: Dimensions fixed.</div>
                            <input type="hidden" id="target-variant-id" value="${product.id}">
                        `}
                    </div>
                    <button class="btn btn-success w-100 mt-3 fw-bold" onclick="QuoteApp.addItem()">
                        ADD TO SOLUTION
                    </button>
                </div>
            </div>
        `;
        $panel.append(html);
    },

    // --- SUBMISSION BRIDGE ---
    addItem() {
        if (this.currentFactory === 'modular') {
            this.addMItem();
        } else {
            this.addPItem();
        }
    },

    async addPItem() {
        const payload = {
            quote_id: this.quoteId,
            solution_id: this.activeSolutionId,
            bundle_id: window.currentBundleId || 0,
            template_id: $("#target-variant-id").val(),
            quantity: $("#cfg-qty").val() || 1
        };
        this._enginePost(`/quoting/api/quotes/${this.quoteId}/add-product/`, payload);
    },

    async addMItem() {
    const payload = {
        // Match the backend data.get() expectations
        solution_id: this.activeSolutionId,
        product_template_id: this.selectedItemId, // Changed from product_id
        length_mm: $("#cfg-L").val() || 0,        // Changed from length
        width_mm: $("#cfg-W").val() || 0,         // Changed from width
        height_mm: $("#cfg-H").val() || 0,        // Changed from height
        quantity: parseInt($("#cfg-qty").val()) || 1
    };
    
    console.log("Stealth Injection Payload:", payload); // Debugging
    this._enginePost(`/quoting/api/quotes/${this.quoteId}/add-modular/`, payload);
},

    _enginePost(url, payload) {
        $.ajax({
            url: url,
            method: "POST",
            headers: { "X-CSRFToken": this.getCookie('csrftoken') },
            data: JSON.stringify(payload),
            contentType: "application/json",
        }).done(() => {
            this.loadQuote(); 
            $("#config-panel").addClass("d-none");
        }).fail((xhr) => {
            alert(`Engine Error: ${xhr.responseJSON?.detail || "Error"}`);
        });
    },

    // --- CANVAS & UI (Now safely inside the object) ---
    renderSolutions() {
        const $list = $("#solution-list").empty();
        this.quote.solutions.forEach(sol => {
            const isActive = this.activeSolutionId === sol.id;
            const item = $(`
                <button class="list-group-item list-group-item-action ${isActive ? 'active bg-primary text-white' : ''} d-flex justify-content-between align-items-center mb-1 rounded border" data-id="${sol.id}">
                    <span class="fw-bold">${sol.name}</span>
                    <span class="badge ${isActive ? 'bg-white text-primary' : 'bg-primary'} rounded-pill">${sol.products?.length || 0}</span>
                </button>
            `);
            item.on("click", () => this.selectSolution(sol.id));
            $list.append(item);
        });
    },

    selectSolution(solutionId) {
        this.activeSolutionId = solutionId;
        const solution = this.quote.solutions.find(s => s.id === solutionId);
        const zoneName = solution ? solution.name : "Active Zone";

        $('#active-zone-badge').text(zoneName.toUpperCase()).removeClass('bg-danger').addClass('bg-success');
        $("#solution-list .list-group-item").removeClass("active bg-primary text-white");
        $(`[data-id="${solutionId}"]`).addClass("active bg-primary text-white");
        
        $("#target-solution-name").text(zoneName);
        this.renderCanvas(solution);
    },

    renderCanvas(solution) {
        const $canvas = $("#solution-canvas").empty();
        if (!solution || !solution.products.length) {
            $canvas.append(`<div class="alert alert-light text-center py-5 border-dashed">Zone is empty.</div>`);
            return;
        }

        solution.products.forEach(prod => {
            const card = $(`
                <div class="card mb-3 border-0 shadow-sm product-card" data-id="${prod.id}">
                    <div class="card-header bg-white d-flex justify-content-between align-items-center">
                        <div>
                            <span class="badge bg-light text-dark border me-2">${prod.quantity}x</span>
                            <strong>${prod.description?.product || 'Item'}</strong>
                        </div>
                        <button class="btn btn-sm btn-link text-decoration-none expand-btn">Show BOM</button>
                    </div>
                    <div class="card-body d-none parts-container bg-light border-top"></div>
                </div>
            `);
            card.find(".expand-btn").on("click", (e) => this.toggleBOM(prod.id, card, $(e.target)));
            $canvas.append(card);
        });
    },

    toggleBOM(productId, card, $btn) {
        const $container = card.find(".parts-container");
        if (!$container.hasClass("d-none")) {
            $container.addClass("d-none");
            $btn.text("Show BOM");
            return;
        }
        $container.removeClass("d-none").html('Loading...');
        $btn.text("Hide BOM");

        $.post({
            url: `/quoting/api/quote-products/${productId}/expand/`,
            headers: { "X-CSRFToken": this.getCookie('csrftoken') }
        }).done((data) => {
            $container.empty();
            let table = `<table class="table table-sm table-borderless mb-0"><tbody>`;
            data.parts.forEach(part => {
                table += `<tr><td class="small">${part.part_name}</td><td class="small text-end text-muted">${part.width}x${part.height}mm</td></tr>`;
            });
            $container.append(table + `</tbody></table>`);
        });
    },

    startSync() {
        setInterval(() => {
            $.get(`/quoting/api/quotes/${this.quoteId}/status/`).done((data) => {
                if (this.quote && data.status !== this.quote.status) this.loadQuote();
            });
        }, 30000);
    },

    renderHeader() {
        $("#quote-number").text(`Quote #${this.quote.quote_number}`);
        $("#quote-grand-total").text(`$${parseFloat(this.quote.grand_total).toLocaleString()}`);
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
    },

    bindEvents() {
        $("#btn-fac-modular").on("click", () => this.setFactory('modular'));
        $("#btn-fac-standard").on("click", () => this.setFactory('standard'));
        $("#filter-cat, #filter-type, #filter-model").on("change", () => this.refreshRegistry());
        
        let timer;
        $("#search-input").on("input", () => {
            clearTimeout(timer);
            timer = setTimeout(() => this.refreshRegistry(), 350);
        });
    }
}; // THE FINAL CLOSING BRACE

$(document).ready(() => QuoteApp.init());