$(document).ready(function() {

    const csrftoken = $("meta[name=csrf-token]").attr("content");
    let currentProductId = null;
    let currentVariantId = null;

    // -------------------------------
    // CSRF setup
    // -------------------------------
    $.ajaxSetup({
        headers: { "X-CSRFToken": csrftoken }
    });

    // -------------------------------
    // Open variant modal
    // -------------------------------
    $(document).on("click", ".manage-variants-btn", function() {
        currentProductId = $(this).data("product-id");
        currentVariantId = null;
        resetVariantForm();
        loadVariants(currentProductId);
    });

    // -------------------------------
    // Load variants for product
    // -------------------------------
    function loadVariants(productId) {
        $.get(`/standprod/api/v1/variants/?product=${productId}`, function(data) {
            renderVariantList(data);
        }).fail(function(xhr) {
            toastr.error("Failed to load variants");
            console.error(xhr);
        });
    }

    // -------------------------------
    // Render variant list in modal
    // -------------------------------
    function renderVariantList(variants) {
        let html = "";
        variants.forEach(v => {
            html += `
            <div class="card mb-2 variant-card" data-variant-id="${v.id}">
                <div class="card-body d-flex justify-content-between">
                    <div>
                        <strong>SKU:</strong> ${v.sku} |
                        <strong>Price:</strong> ${v.selling_price} |
                        <strong>Dimensions:</strong> ${v.length} x ${v.width} x ${v.height}
                    </div>
                    <div>
                        <button class="btn btn-sm btn-warning edit-variant-btn" data-variant-id="${v.id}">Edit</button>
                        <button class="btn btn-sm btn-danger delete-variant-btn" data-variant-id="${v.id}">Delete</button>
                    </div>
                </div>
            </div>`;
        });

        html += `<button class="btn btn-success btn-sm mt-2" id="addVariantBtn">Add Variant</button>`;
        $("#variantList").html(html);
    }

    // -------------------------------
    // Reset variant form
    // -------------------------------
    function resetVariantForm() {
        $("#variantForm")[0].reset();
        $("#attributeContainer").html("");
        $("#imageContainer").html("");
    }

    // -------------------------------
    // Add Variant button click
    // -------------------------------
    $(document).on("click", "#addVariantBtn", function() {
        currentVariantId = null;
        resetVariantForm();
        $("#variantModalLabel").text("Add Variant");
        $("#variantFormWrapper").show();
    });

    // -------------------------------
    // Edit Variant
    // -------------------------------
    $(document).on("click", ".edit-variant-btn", function() {
        const variantId = $(this).data("variant-id");
        currentVariantId = variantId;
        $("#variantFormWrapper").show();
        $("#variantModalLabel").text("Edit Variant");

        $.get(`/standprod/api/v1/variants/${variantId}/`, function(data) {
            $("#variantLength").val(data.length);
            $("#variantWidth").val(data.width);
            $("#variantHeight").val(data.height);
            $("#variantWeight").val(data.weight);
            $("#variantSellingPrice").val(data.selling_price);
            $("#variantPurchasePrice").val(data.purchase_price);
            $("#variantActive").prop("checked", data.is_active);

            // Set measurement & billing unit selects
            $("#measurementUnitSelect").val(data.measurement_unit.id).trigger('change');
            $("#billingUnitSelect").val(data.billing_unit.id).trigger('change');

            // Render attributes
            $("#attributeContainer").html("");
            data.attributes.forEach(attr => {
                addAttributeRow(attr.attribute, attr.value);
            });

            // Render images
            $("#imageContainer").html("");
            data.images.forEach(img => {
                addImagePreview(img.id, img.image);
            });

        }).fail(function(xhr) {
            toastr.error("Failed to load variant");
            console.error(xhr);
        });
    });

    // -------------------------------
    // Delete Variant
    // -------------------------------
    $(document).on("click", ".delete-variant-btn", function() {
        const variantId = $(this).data("variant-id");
        if (!confirm("Are you sure you want to delete this variant?")) return;

        $.ajax({
            url: `/standprod/api/v1/variants/${variantId}/`,
            method: "DELETE",
            success: function() {
                toastr.success("Variant deleted");
                loadVariants(currentProductId);
            },
            error: function(xhr) {
                toastr.error("Failed to delete variant");
                console.error(xhr);
            }
        });
    });

    // -------------------------------
    // Add attribute row
    // -------------------------------
    function addAttributeRow(attributeId = "", value = "") {
        const html = `
        <div class="input-group mb-2 attribute-row">
            <select class="form-select attribute-select" name="attribute">
                <!-- Populate dynamically -->
            </select>
            <input type="text" class="form-control attribute-value" name="value" value="${value}" placeholder="Value">
            <button class="btn btn-danger remove-attribute-btn" type="button">&times;</button>
        </div>`;
        $("#attributeContainer").append(html);
        $(".attribute-select").last().val(attributeId).trigger('change');
    }

    $(document).on("click", ".remove-attribute-btn", function() {
        $(this).closest(".attribute-row").remove();
    });

    $("#addAttributeBtn").click(function() {
        addAttributeRow();
    });

    // -------------------------------
    // Add image preview
    // -------------------------------
    function addImagePreview(id, url) {
        const html = `<div class="image-preview mb-2" data-image-id="${id}">
            <img src="${url}" alt="Image" style="height:60px;">
            <button class="btn btn-sm btn-danger remove-image-btn">&times;</button>
        </div>`;
        $("#imageContainer").append(html);
    }

    $(document).on("click", ".remove-image-btn", function() {
        $(this).closest(".image-preview").remove();
    });

    // -------------------------------
    // Submit Variant Form
    // -------------------------------
    $("#variantForm").submit(function(e) {
        e.preventDefault();

        let attributes = [];
        $("#attributeContainer .attribute-row").each(function() {
            const attrId = $(this).find(".attribute-select").val();
            const val = $(this).find(".attribute-value").val();
            attributes.push({ attribute: parseInt(attrId), value: val });
        });

        const formData = {
            product_id: currentProductId,
            length: $("#variantLength").val(),
            width: $("#variantWidth").val(),
            height: $("#variantHeight").val(),
            weight: $("#variantWeight").val(),
            purchase_price: $("#variantPurchasePrice").val(),
            selling_price: $("#variantSellingPrice").val(),
            is_active: $("#variantActive").is(":checked"),
            measurement_unit_id: $("#measurementUnitSelect").val(),
            billing_unit_id: $("#billingUnitSelect").val(),
            attribute_payload: attributes
        };

        let method = currentVariantId ? "PUT" : "POST";
        let url = currentVariantId ? `/standprod/api/v1/variants/${currentVariantId}/` : "/standprod/api/v1/variants/";

        $.ajax({
            url: url,
            method: method,
            contentType: "application/json",
            data: JSON.stringify(formData),
            success: function(data) {
                toastr.success(`Variant ${currentVariantId ? "updated" : "created"}`);
                $("#variantFormWrapper").hide();
                loadVariants(currentProductId);
            },
            error: function(xhr) {
                toastr.error("Failed to save variant");
                console.error(xhr);
            }
        });
    });

    // -------------------------------
    // Populate selects for measurement, billing, attributes
    // -------------------------------
    function populateSelects() {
    $.get("/standprod/api/v1/measurement-units/", function(data) {
        if (Array.isArray(data)) {
            $("#measurementUnitSelect").html(data.map(u => `<option value="${u.id}">${u.name}</option>`));
        } else if (data && Array.isArray(data.results)) {
            // If the response is wrapped in an object with a 'results' property
            $("#measurementUnitSelect").html(data.results.map(u => `<option value="${u.id}">${u.name}</option>`));
        } else {
            console.error('Unexpected response structure for measurement-units:', data);
        }
    });

    $.get("/standprod/api/v1/billing-units/", function(data) {
        if (Array.isArray(data)) {
            $("#billingUnitSelect").html(data.map(u => `<option value="${u.id}">${u.name}</option>`));
        } else if (data && Array.isArray(data.results)) {
            $("#billingUnitSelect").html(data.results.map(u => `<option value="${u.id}">${u.name}</option>`));
        } else {
            console.error('Unexpected response structure for billing-units:', data);
        }
    });

    $.get("/standprod/api/v1/attribute-definitions/", function(data) {
        if (Array.isArray(data)) {
            $(".attribute-select").html(data.map(a => `<option value="${a.id}">${a.name}</option>`));
        } else if (data && Array.isArray(data.results)) {
            $(".attribute-select").html(data.results.map(a => `<option value="${a.id}">${a.name}</option>`));
        } else {
            console.error('Unexpected response structure for attribute-definitions:', data);
        }
    });
}


    populateSelects();
});
