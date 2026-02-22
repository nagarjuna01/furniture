/**
 * Global Engine Workspace - v1.2
 * Consolidates Standard Catalog & Modular DNA
 */
const QuoteApp = {
    quoteId: $("#quote-app").data("quote-id"),
    quote: null,
    activeSolutionId: null,
    selectedItemId: null,
    currentFactory: 'modular', // Default mode
    currentProductType: null, // 'standard' or 'modular'
    lastActiveProduct: null,
    lastActiveParts: [],

    init() {
        this.loadQuote();
        this.bindEvents();
        this.refreshRegistry();
        this.startSync();
    },

    // --- DATA LOADING ---
    loadQuote() {
        $.ajax({
            url: `/quoting/api/quotes/${this.quoteId}/`,
            method: "GET",
        })
        .done((data) => {
            this.quote = data;
            this.renderHeader();
            this.renderSolutions();
            // Auto-select first solution if none active
            if (!this.activeSolutionId && data.solutions?.length > 0) {
                this.selectSolution(data.solutions[0].id);
            } else if (this.activeSolutionId) {
                this.selectSolution(this.activeSolutionId);
            }
        })
        .fail(() => console.error("Engine Sync Failure. Check DB Connection."));
    },

    // --- RENDERING ---
    renderHeader() {
        $("#quote-number").text(`Quote #${this.quote.quote_number}`);
        $("#quote-status").text(this.quote.status.toUpperCase());
        $("#quote-grand-total").text(`$${parseFloat(this.quote.grand_total).toLocaleString()}`);

        if (this.quote.client_detail) {
            $("#client-name-display").text(this.quote.client_detail.name);
            $("#client-email-display").text(this.quote.client_detail.email || "No Email");
            $("#client-phone-display").text(this.quote.client_detail.phone || "No Phone");
            $("#client-tax-display").text(this.quote.client_detail.tax_number || "N/A");
        }
        
        const isDraft = this.quote.status === 'draft';
        $("#btn-approve, #btn-lock").toggleClass("d-none", !isDraft);
        $("#btn-pdf").toggleClass("d-none", isDraft).attr("href", `/quoting/api/quotes/${this.quoteId}/pdf/`);
    },

    renderSolutions() {
        const $list = $("#solution-list").empty();
        this.quote.solutions.forEach(sol => {
            const activeClass = this.activeSolutionId === sol.id ? 'active bg-primary text-white' : '';
            const item = $(`
                <button class="list-group-item list-group-item-action ${activeClass} d-flex justify-content-between align-items-center" data-id="${sol.id}">
                    <span>${sol.name}</span>
                    <span class="badge ${this.activeSolutionId === sol.id ? 'bg-white text-primary' : 'bg-primary'} rounded-pill">
                        ${sol.products?.length || 0}
                    </span>
                </button>
            `);

            item.on("click", () => this.selectSolution(sol.id));
            $list.append(item);
        });
    },

    selectSolution(solutionId) {
        this.activeSolutionId = solutionId;
        $("#solution-list .list-group-item").removeClass("active bg-primary text-white");
        $(`[data-id="${solutionId}"]`).addClass("active bg-primary text-white");
        
        const solution = this.quote.solutions.find(s => s.id === solutionId);
        $("#target-solution-name").text(solution ? solution.name : "");
        this.renderCanvas(solution);
    },

    renderCanvas(solution) {
        const $canvas = $("#solution-canvas").empty();
        if (!solution || !solution.products.length) {
            $canvas.append(`
                <div class="card border-0 shadow-sm">
                    <div class="card-body text-center py-5">
                        <h5 class="text-muted">Zone is Empty</h5>
                        <button class="btn btn-primary btn-sm mt-2" onclick="$('#addProductModal').modal('show')">
                            Add First Item
                        </button>
                    </div>
                </div>`);
            return;
        }

        solution.products.forEach(prod => {
            const card = $(`
                <div class="card mb-3 border-0 shadow-sm product-card" data-id="${prod.id}">
                    <div class="card-header bg-white d-flex justify-content-between align-items-center">
                        <div>
                            <span class="badge bg-light text-dark border me-2">${prod.quantity}x</span>
                            <strong>${prod.description?.product || 'Standard Item'}</strong>
                            <small class="text-muted ms-2">(${prod.length_mm}x${prod.width_mm}x${prod.height_mm}mm)</small>
                        </div>
                        <button class="btn btn-sm btn-link text-decoration-none expand-btn">Show BOM</button>
                    </div>
                    <div class="card-body d-none parts-container bg-light border-top">
                        <div class="text-center py-2"><div class="spinner-border spinner-border-sm text-primary"></div></div>
                    </div>
                </div>
            `);

            card.find(".expand-btn").on("click", (e) => this.toggleBOM(prod.id, card, $(e.target)));
            $canvas.append(card);
        });
    },

    // --- SEARCH & ADD LOGIC ---
    searchItems(query) {
        if (query.length < 2) {
            $("#search-results").addClass("d-none").empty();
            return;
        }
        
        // Handshake: Search both Static Bundles and Modular Templates
        const stdSearch = $.get(`/products1/v1/product-variants/?search=${query}`);
        const modSearch = $.get(`/modularcalc/api/products/?search=${query}`);

        $.when(stdSearch, modSearch).done((stdData, modData) => {
            const $results = $("#search-results").removeClass("d-none").empty();
            
            // Standard Catalog
            stdData[0].forEach(b => {
                const btn = $(`<button class="list-group-item list-group-item-action d-flex justify-content-between">
                    <span><i class="fas fa-box me-2"></i>${b.name}</span>
                    <span class="badge bg-success-subtle text-success">STOCK</span>
                </button>`);
                btn.on("click", () => this.prepareItem(b.id, 'standard'));
                $results.append(btn);
            });

            // Modular DNA
            modData[0].forEach(t => {
                const btn = $(`<button class="list-group-item list-group-item-action d-flex justify-content-between">
                    <span><i class="fas fa-drafting-compass me-2"></i>${t.name}</span>
                    <span class="badge bg-info-subtle text-info">MODULAR</span>
                </button>`);
                btn.on("click", () => this.prepareItem(t.id, 'modular'));
                $results.append(btn);
            });
        });
    },

    prepareItem(id, type) {
        this.selectedItemId = id;
        this.currentProductType = type;
        $("#search-results").addClass("d-none");
        $("#config-panel").removeClass("d-none");
        $("#btn-save-item").removeClass("d-none");
        
        // Modular items require dimensions
        if (type === 'modular') {
            $("#inp-L, #inp-W, #inp-H").prop('disabled', false).val(1000);
        } else {
            $("#inp-L, #inp-W, #inp-H").prop('disabled', true).val(0);
        }
    },

    addItem() {
        const isStd = this.currentProductType === 'standard';
        const url = `/quoting/api/quotes/${this.quoteId}/${isStd ? 'add_bundle/' : 'add_modular/'}`;

        const payload = {
            solution_id: this.activeSolutionId,
            quantity: $("#inp-Qty").val() || 1,
            [isStd ? 'bundle_id' : 'template_id']: this.selectedItemId,
            length_mm: $("#inp-L").val(),
            width_mm: $("#inp-W").val(),
            height_mm: $("#inp-H").val()
        };

        $.ajax({
            url: url,
            method: "POST",
            headers: { "X-CSRFToken": this.getCookie('csrftoken') },
            data: JSON.stringify(payload),
            contentType: "application/json",
        }).done(() => {
            $("#addProductModal").modal("hide");
            $("#config-panel").addClass("d-none");
            $("#search-input").val("");
            this.loadQuote();
        }).fail((xhr) => alert("Engine Error: " + JSON.stringify(xhr.responseJSON)));
    },

    // --- BOM EXPANSION ---
    toggleBOM(productId, card, $btn) {
        const $container = card.find(".parts-container");
        if (!$container.hasClass("d-none")) {
            $container.addClass("d-none");
            $btn.text("Show BOM");
            return;
        }

        $container.removeClass("d-none");
        $btn.text("Hide BOM");

        $.post({
            url: `/quoting/api/quote-products/${productId}/expand/`,
            headers: { "X-CSRFToken": this.getCookie('csrftoken') }
        }).done((data) => {
            $container.empty();
            let table = `<table class="table table-sm table-borderless mb-0"><tbody>`;
            data.parts.forEach(part => {
                table += `<tr>
                    <td class="small">${part.part_name}</td>
                    <td class="small text-end text-muted">${part.width} x ${part.height} mm</td>
                </tr>`;
            });
            table += `</tbody></table>`;
            $container.append(table);
        });
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

    startSync() {
        setInterval(() => {
            $.get(`/quoting/api/quotes/${this.quoteId}/status/`).done((data) => {
                if (this.quote && data.status !== this.quote.status) this.loadQuote();
            });
        }, 30000);
    },

    bindEvents() {
        $("#search-input").on("input", (e) => this.searchItems($(e.target).val()));
        $("#btn-save-item").on("click", () => this.addItem());
        
        $("#btn-add-solution").on("click", () => $("#addSolutionModal").modal("show"));
        $("#btn-save-solution").on("click", () => {
            const name = $("#new-solution-name").val();
            if (!name) return;
            $.ajax({
                url: `/quoting/api/quotes/${this.quoteId}/add_solution/`,
                method: "POST",
                headers: { "X-CSRFToken": this.getCookie('csrftoken') }, 
                data: JSON.stringify({ name: name }),
                contentType: "application/json",
            }).done(() => {
                $("#addSolutionModal").modal("hide");
                this.loadQuote();
            });
        });
        
        $("#btn-approve").on("click", () => $.post({url: `/quoting/api/quotes/${this.quoteId}/approve/`, headers: {"X-CSRFToken": this.getCookie('csrftoken')}}).done(() => this.loadQuote()));
        $("#btn-lock").on("click", () => $.post({url: `/quoting/api/quotes/${this.quoteId}/lock/`, headers: {"X-CSRFToken": this.getCookie('csrftoken')}}).done(() => this.loadQuote()));
    }
};

$(document).ready(() => QuoteApp.init());