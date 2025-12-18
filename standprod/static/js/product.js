$(document).ready(function() {

    // -------------------------------
    // Global variables
    // -------------------------------
    const csrftoken = $("meta[name=csrf-token]").attr("content");
    let products = []; // store fetched products
    let currentProductId = null; // product id for variant modal

    // -------------------------------
    // AJAX Setup with CSRF
    // -------------------------------
    $.ajaxSetup({
        headers: { "X-CSRFToken": csrftoken }
    });

    // -------------------------------
    // Fetch all products
    // -------------------------------
    function fetchProducts() {
        $.get("/standprod/api/v1/products/", function(data) {
            products = data;
            renderProducts(products);
        }).fail(function(xhr) {
            toastr.error("Failed to fetch products");
            console.error(xhr);
        });
    }

    // -------------------------------
    // Render products (cards)
    // -------------------------------
    function renderProducts(productsList) {
    console.log("Product API Response:", productsList);

    // Support both paginated and non-paginated API responses
    const list = productsList.results || productsList;

    if (!Array.isArray(list)) {
        console.error("❌ Error: Invalid product list format:", productsList);
        return;
    }

    let html = "";

    list.forEach(p => {
        const img = (p.images && p.images.length)
            ? p.images[0].image
            : "/static/images/placeholder.png";

        html += `
        <div class="col-md-4 mb-3">
            <div class="card h-100 shadow-sm">
                <img src="${img}" class="card-img-top" alt="${p.name}">
                <div class="card-body">
                    <h5 class="card-title">${p.name}</h5>
                    <p class="card-text">SKU: ${p.sku ?? "—"}</p>
                    <p class="card-text">Variants: ${p.variants?.length ?? 0}</p>

                    <button class="btn btn-primary btn-sm manage-variants-btn"
                            data-product-id="${p.id}"
                            data-bs-toggle="modal"
                            data-bs-target="#variantModal">
                        Manage Variants
                    </button>
                </div>
            </div>
        </div>`;
    });

    $("#product-cards").html(html);
}

    // -------------------------------
    // Filters
    // -------------------------------
    $("#filterType").change(applyFilters);
    $("#filterModel").change(applyFilters);
    $("#searchProduct").on("input", applyFilters);

    function applyFilters() {
        let typeId = $("#filterType").val();
        let modelId = $("#filterModel").val();
        let search = $("#searchProduct").val().toLowerCase();

        const filtered = products.filter(p => {
            return (!typeId || p.type.id == typeId) &&
                   (!modelId || p.model.id == modelId) &&
                   (!search || p.name.toLowerCase().includes(search));
        });

        renderProducts(filtered);
    }

    // -------------------------------
    // Variant Modal: Load product variants
    // -------------------------------
    $(document).on("click", ".manage-variants-btn", function() {
        currentProductId = $(this).data("product-id");
        loadVariants(currentProductId);
    });

    function loadVariants(productId) {
        const product = products.find(p => p.id == productId);
        if (!product) return;

        let html = "";
        product.variants.forEach(v => {
            html += `
            <div class="card mb-2">
                <div class="card-body d-flex justify-content-between">
                    <span>SKU: ${v.sku} | Price: ${v.selling_price}</span>
                    <div>
                        <button class="btn btn-sm btn-warning edit-variant-btn" data-variant-id="${v.id}">Edit</button>
                        <button class="btn btn-sm btn-danger delete-variant-btn" data-variant-id="${v.id}">Delete</button>
                    </div>
                </div>
            </div>`;
        });

        $("#variantForm").html(html + `<button class="btn btn-success btn-sm" id="addVariantBtn">Add Variant</button>`);
    }

    // -------------------------------
    // Add Variant
    // -------------------------------
    $(document).on("click", "#addVariantBtn", function() {
        let formHtml = `
            <form id="newVariantForm">
                <input type="hidden" name="product_id" value="${currentProductId}">
                <div class="mb-2">
                    <label>Length</label>
                    <input type="number" name="length" class="form-control" required>
                </div>
                <div class="mb-2">
                    <label>Width</label>
                    <input type="number" name="width" class="form-control" required>
                </div>
                <div class="mb-2">
                    <label>Height</label>
                    <input type="number" name="height" class="form-control" required>
                </div>
                <div class="mb-2">
                    <label>Selling Price</label>
                    <input type="number" name="selling_price" class="form-control" required>
                </div>
                <button class="btn btn-primary btn-sm" type="submit">Save Variant</button>
            </form>`;
        $("#variantForm").html(formHtml);
    });

    // -------------------------------
    // Submit new variant
    // -------------------------------
    $(document).on("submit", "#newVariantForm", function(e) {
        e.preventDefault();
        const formData = $(this).serializeJSON(); // serializeJSON plugin recommended

        $.ajax({
            url: "/standprod/api/v1/variants/",
            method: "POST",
            data: JSON.stringify(formData),
            contentType: "application/json",
            success: function(data) {
                toastr.success("Variant created");
                $("#variantModal").modal('hide');
                fetchProducts();
            },
            error: function(xhr) {
                toastr.error("Failed to create variant");
                console.error(xhr);
            }
        });
    });

    // -------------------------------
    // Edit / Delete variants
    // -------------------------------
    $(document).on("click", ".delete-variant-btn", function() {
        const variantId = $(this).data("variant-id");
        if (!confirm("Delete this variant?")) return;

        $.ajax({
            url: `/standprod/api/v1/variants/${variantId}/`,
            method: "DELETE",
            success: function() {
                toastr.success("Variant deleted");
                fetchProducts();
                loadVariants(currentProductId);
            },
            error: function(xhr) {
                toastr.error("Failed to delete variant");
                console.error(xhr);
            }
        });
    });

    // TODO: Add edit variant logic similar to add variant

    // -------------------------------
    // Initialize
    // -------------------------------
    fetchProducts();
});
