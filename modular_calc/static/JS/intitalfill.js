// Only global variables & initialization
const allData = window.allData || { hardware: [], edgebands: [], materials: [] };
const selected = {
    materials: [],
    defaultMaterialId: null,
    edgebands: {
        top: { whitelist: [], default: null },
        right: { whitelist: [], default: null },
        bottom: { whitelist: [], default: null },
        left: { whitelist: [], default: null }
    },
    partHardware: {},
    productHardware: {},
};

window.savedGeometry = {};  // geometry memory
window._uploadedSVG = null; // temporary storage for geometry modal


