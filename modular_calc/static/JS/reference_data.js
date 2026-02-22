window.refData = {
    categories: [],
    types: [],
    models: []
};

async function fetchAllPages(url) {
    let results = [];
    let nextUrl = url;

    while (nextUrl) {
        const response = await fetch(nextUrl);
        if (!response.ok) {
            throw new Error(`Failed to fetch ${nextUrl}`);
        }

        const data = await response.json();
        results = results.concat(data.results);
        nextUrl = data.next; // null when no more pages
    }

    return results;
}


async function loadReferenceData() {
    const [cats, types, models] = await Promise.all([
        fetchAllPages("/modularcalc/api/product-categories/"),
        fetchAllPages("/modularcalc/api/product-types/"),
        fetchAllPages("/modularcalc/api/product-models/")
    ]);

    refData.categories = cats;
    refData.types = types;
    refData.models = models;
}
function loadCategoryDropdown(selectId) {
    const el = document.getElementById(selectId);
    if (!el) return;

    el.innerHTML = `<option value="">Select Category</option>`;
    refData.categories.forEach(c =>
        el.innerHTML += `<option value="${c.id}">${c.name}</option>`
    );
}

function loadTypeDropdown(categoryId, selectId) {
    const el = document.getElementById(selectId);
    if (!el) return;

    el.innerHTML = `<option value="">Select Type</option>`;
    refData.types
        .filter(t => t.category == categoryId)
        .forEach(t =>
            el.innerHTML += `<option value="${t.id}">${t.name}</option>`
        );

    el.disabled = false;
}

function loadModelDropdown(typeId, selectId) {
    const el = document.getElementById(selectId);
    if (!el) return;

    el.innerHTML = `<option value="">Select Model</option>`;
    refData.models
        .filter(m => m.type == typeId)
        .forEach(m =>
            el.innerHTML += `<option value="${m.id}">${m.name}</option>`
        );

    el.disabled = false;
}
document.addEventListener("DOMContentLoaded", async () => {
       
    await loadReferenceData();

    loadCategoryDropdown("categoryselect");

    document.getElementById("categoryselect").addEventListener("change", e => {
        loadTypeDropdown(e.target.value, "type-select");
        document.getElementById("model-select").innerHTML = "";
    });

    document.getElementById("type-select").addEventListener("change", e => {
        loadModelDropdown(e.target.value, "model-select");
    });
});
