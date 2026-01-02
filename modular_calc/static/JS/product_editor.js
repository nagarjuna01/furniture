document.addEventListener("DOMContentLoaded", async () => {
    await preloadReferenceData();
    initAddProductDropdowns();
});

function initAddProductDropdowns() {
    loadCategoriesDropdown();
    
    const cat = document.getElementById("categoryselect");
    const type = document.getElementById("type-select");
    const model = document.getElementById("model-select");

    cat.onchange = async () => {
        type.disabled = true;
        model.disabled = true;
        await loadTypesDropdownByCategory(cat.value);
    };

    type.onchange = async () => {
        model.disabled = true;
        await loadModelsDropdownByType(type.value);
    };
}
