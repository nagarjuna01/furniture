
   // ----------------------------
    // FETCH & FILTERS
    // ----------------------------
    async function fetchAllPages(url) {
        let results = [], nextUrl = url;
        while (nextUrl) {
            try {
                const res = await fetch(nextUrl);
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                if (data.results) results.push(...data.results);
                nextUrl = data.next;
            } catch(err) {
                console.error(`Error fetching ${nextUrl}`, err);
                break;
            }
        }
        return results;
    }

    async function preloadAllData() {
        [allData.materials, allData.edgebands, allData.hardware] = await Promise.all([
            fetchAllPages('/material/v1/woodens/'),
            fetchAllPages('/material/v1/edgebands/'),
            fetchAllPages('/material/v1/hardware/')
        ]);
        
        initAllFilters();
    }

    function fillSelect(selectId, values) {
        const select = document.getElementById(selectId);
        if (!select) return;
        select.querySelectorAll('option:not(:first-child)').forEach(o => o.remove());
        values.forEach(v => select.appendChild(new Option(v, v)));
    }

    function initAllFilters() {
        initMaterialFilters();
        initEdgebandFilters();
        initHardwareFilters();
        renderMaterialTable();
        ['top','right','bottom','left'].forEach(side => renderEdgebandSide(side));
    renderSelectedEdgebands();
        
    }
