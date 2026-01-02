$(document).ready(function () {
    console.log("Brand list JS loaded");

    loadBrands();
});

function loadBrands() {
    $.ajax({
        url: "/material/v1/brands/",
        method: "GET",
        success: function (response) {
            console.log("API response:", response);

            const tbody = $("#brand-table tbody");
            tbody.empty();

            response.results.forEach((brand, index) => {
                tbody.append(`
                    <tr>
                        <td>${index + 1}</td>
                        <td>${brand.name}</td>
                    </tr>
                `);
            });
        },
        error: function (xhr) {
            console.error("Failed to load brands", xhr.status, xhr.responseText);
        }
    });
}
