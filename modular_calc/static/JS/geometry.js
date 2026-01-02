function resetGeometryFields(svgPreview, lengthEq, widthEq, qtyEq) {
    svgPreview.innerHTML = `<p class="text-muted mb-0">SVG preview will appear here</p>`;
    window._uploadedSVG = null;
    lengthEq.value = widthEq.value = qtyEq.value = "";
}  
    
window.openGeometryModal = function(initialData = null) {
        const svgPreview = document.getElementById("geom-svg-preview");
        const lengthEq = document.getElementById("geom-length-eq");
        const widthEq  = document.getElementById("geom-width-eq");
        const qtyEq    = document.getElementById("geom-qty-eq");

        if (!svgPreview || !lengthEq || !widthEq || !qtyEq) return;

        resetGeometryFields(svgPreview, lengthEq, widthEq, qtyEq);

        if (initialData) {
            lengthEq.value = initialData.lengthEq || "";
            widthEq.value  = initialData.widthEq || "";
            qtyEq.value    = initialData.qtyEq || "";
            if (initialData.svg) {
                svgPreview.innerHTML = initialData.svg;
                window._uploadedSVG = initialData.svg;
            }
        }

        showModal("geometryModal");
    };

    // SVG Upload & Save
    const svgUpload = document.getElementById("geom-svg-upload");
    svgUpload?.addEventListener("change", function() {
        const file = this.files[0];
        if (!file || !file.name.endsWith(".svg")) return alert("Only SVG files allowed");
        const reader = new FileReader();
        reader.onload = e => {
            window._uploadedSVG = e.target.result;
            document.getElementById("geom-svg-preview").innerHTML = window._uploadedSVG;
        };
        reader.readAsText(file);
});

document.getElementById("save-geometry-btn")?.addEventListener("click", () => {
    const lengthEq = document.getElementById("geom-length-eq").value.trim();
    const widthEq  = document.getElementById("geom-width-eq").value.trim();
    const qtyEq    = document.getElementById("geom-qty-eq").value.trim();
    const svg      = window._uploadedSVG || null;

    if (!svg && !lengthEq && !widthEq && !qtyEq) return alert("Provide SVG or equations");

    const geometry = { svg, lengthEq, widthEq, qtyEq };
    document.dispatchEvent(new CustomEvent("geometrySaved", { detail: geometry }));
    hideModal("geometryModal");
});
