/* ============================================================
   ASSETS LOGIC (SVG & 3D)
============================================================ */

function initAssetsLogic() {
    const svgInput = document.getElementById('two-d-svg-input');
    const threeDInput = document.getElementById('three-d-asset-input');

    // Ensure state exists
    if (!window.productSubmissionState.assets) {
        window.productSubmissionState.assets = {
            svg_template: "",
            three_d_model: ""
        };
    }

    // Sync SVG input to memory
    svgInput?.addEventListener('input', (e) => {
        window.productSubmissionState.assets.svg_template = e.target.value;
    });

    // Sync 3D path input to memory
    threeDInput?.addEventListener('input', (e) => {
        window.productSubmissionState.assets.three_d_model = e.target.value;
    });
}

// Call this in your main DOMContentLoaded listener
document.addEventListener('DOMContentLoaded', initAssetsLogic);