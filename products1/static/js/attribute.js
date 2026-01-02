// attribute.js
// =========================
// Attribute Definition CRUD
// =========================

(function () {
    "use strict";

    const API_URL = "/products1/v1/attributes/";

    // -----------------------
    // CSRF
    // -----------------------
    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    // -----------------------
    // Modal Helpers
    // -----------------------
    const modalEl = document.getElementById("attributeModal");
    const attributeModal = new bootstrap.Modal(modalEl);

    function resetForm() {
        $("#form-attribute")[0].reset();
        $("#attribute-id").val("");
        $("#choice-container").hide();
    }

    // -----------------------
    // Load Attributes (READ)
    // -----------------------
    function loadAttributes() {
    $.ajax({
        url: API_URL,
        method: "GET",
        success: function (response) {
            console.log("ATTRIBUTES RESPONSE:", response);

            const rows = response.results || [];   // ✅ PAGINATION FIX
            const tbody = $("#table-attributes tbody");
            tbody.empty();

            if (!rows.length) {
                tbody.append(`
                    <tr>
                        <td colspan="4" class="text-center text-muted">
                            No attributes found
                        </td>
                    </tr>
                `);
                return;
            }

            rows.forEach(attr => {
                tbody.append(`
                    <tr>
                        <td>${attr.name}</td>
                        <td>${attr.field_type}</td>
                        <td>${attr.choices?.join(", ") || "-"}</td>
                        <td>
                            <button class="btn btn-sm btn-warning btn-edit"
                                data-id="${attr.id}">
                                Edit
                            </button>
                            <button class="btn btn-sm btn-danger btn-delete"
                                data-id="${attr.id}">
                                Delete
                            </button>
                        </td>
                    </tr>
                `);
            });
        }
    }).fail(err => {
        console.error("LOAD ATTRIBUTES FAILED:", err);
    });
}

    // -----------------------
    // Field Type Change
    // -----------------------
    $("#attribute-type").on("change", function () {
        const type = $(this).val();
        $("#choice-container").toggle(type === "choice");
    });

    // -----------------------
    // Add Attribute
    // -----------------------
    $("#btn-add-attribute-definition").on("click", function () {
        resetForm();
        attributeModal.show();
    });

    // -----------------------
    // Create / Update
    // -----------------------
    $("#form-attribute").on("submit", function (e) {
        e.preventDefault();

        const id = $("#attribute-id").val();
        const isEdit = Boolean(id);

        let payload = {
            name: $("#attribute-name").val(),
            field_type: $("#attribute-type").val(),
            choices: []
        };

        if (payload.field_type === "choice") {
            try {
                payload.choices = JSON.parse($("#attribute-choices").val());
            } catch (err) {
                alert("Invalid JSON format for choices");
                console.error("CHOICES JSON ERROR:", err);
                return;
            }
        }

        console.log("SUBMIT PAYLOAD:", payload);

        $.ajax({
            url: isEdit ? `${API_URL}${id}/` : API_URL,
            method: isEdit ? "PUT" : "POST",
            headers: {
                "X-CSRFToken": getCSRFToken()
            },
            contentType: "application/json",
            data: JSON.stringify(payload),
            success: function () {
                attributeModal.hide();
                loadAttributes();
            }
        }).fail(err => {
            console.error("SAVE FAILED:", err.responseJSON);
            alert(JSON.stringify(err.responseJSON));
        });
    });

    // -----------------------
    // Edit Attribute
    // -----------------------
    $(document).on("click", ".btn-edit", function () {
        const id = $(this).data("id");

        $.get(`${API_URL}${id}/`, function (data) {
            console.log("EDIT DATA:", data);

            $("#attribute-id").val(data.id);
            $("#attribute-name").val(data.name);
            $("#attribute-type").val(data.field_type).trigger("change");
            $("#attribute-choices").val(JSON.stringify(data.choices));

            attributeModal.show();
        }).fail(err => {
            console.error("EDIT LOAD FAILED:", err);
        });
    });

    // -----------------------
    // Delete Attribute
    // -----------------------
    $(document).on("click", ".btn-delete", function () {
        const id = $(this).data("id");

        if (!confirm("Are you sure you want to delete this attribute?")) return;

        $.ajax({
            url: `${API_URL}${id}/`,
            method: "DELETE",
            headers: {
                "X-CSRFToken": getCSRFToken()
            },
            success: function () {
                loadAttributes();
            }
        }).fail(err => {
            console.error("DELETE FAILED:", err);
        });
    });

    // -----------------------
    // Init
    // -----------------------
    document.addEventListener("DOMContentLoaded", function () {
        loadAttributes();
    });

})();
