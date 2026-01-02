async function fetchAllPages(url) {
    console.log(`[FETCH] Start fetching: ${url}`);
    let results = [], nextUrl = url;
    while (nextUrl) {
        try {
            const res = await fetch(nextUrl, { headers: { "Accept": "application/json" }, credentials: "same-origin" });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            if (data.results) {
                console.log(`[FETCH] Fetched ${data.results.length} items from ${nextUrl}`);
                results.push(...data.results);
            }
            nextUrl = data.next;
        } catch (err) {
            console.error(`[FETCH] Error fetching ${nextUrl}`, err);
            break;
        }
    }
    console.log(`[FETCH] Finished fetching ${url}, total: ${results.length}`);
    return results;
}

async function preloadAllData() {
    console.log("[ADD-PRODUCT] preloadAllData started");

    try {
        [
            allData.materials,
            allData.edgebands,
            allData.hardware
        ] = await Promise.all([
            // fetchAllPages('/material/v1/woodens/'),
            fetchAllPages('/material/v1/edgebands/'),
            fetchAllPages('/material/v1/hardware/')
        ]);

        console.log("[preloadAllData] All data loaded:");
        console.log("materials:", allData.materials.length, allData.materials);
        console.log("edgebands:", allData.edgebands.length, allData.edgebands);
        console.log("hardware:", allData.hardware.length, allData.hardware);

        console.log("[preloadAllData] Initializing all filters");
        initAllFilters();
        console.log("[preloadAllData] Filters initialized");

    } catch (err) {
        console.error("[preloadAllData] Failed", err);
        if (window.showToast) {
            showToast("Failed to load master data", "danger");
        }
    }
}

function fillSelect(selectId, values, valueKey = "id", labelKey = "name") {
    const select = document.getElementById(selectId);
    if (!select) return console.warn(`[fillSelect] Select element not found: ${selectId}`);

    console.log(`[fillSelect] Filling select ${selectId} with ${values.length} options`);
    select.querySelectorAll('option:not(:first-child)').forEach(o => o.remove());

    values.forEach(v => {
        if (typeof v === "object") {
            select.appendChild(new Option(v[labelKey], v[valueKey]));
        } else {
            select.appendChild(new Option(v, v));
        }
    });
}

function initAllFilters() {
    console.log("[initAllFilters] Initializing filters");

    // if (window.initMaterialFilters) initMaterialFilters();
    if (window.initEdgebandFilters) initEdgebandFilters();
    if (window.initHardwareFilters) initHardwareFilters();
}