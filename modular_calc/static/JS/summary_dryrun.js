/* ============================================================
   DRY RUN / PREVIEW LOGIC (FINAL STABLE VERSION)
============================================================ */

async function runProductionDryRun() {
    const summaryContainer = document.getElementById('cutlist-container');
    
    // 1. Use the correct state from your modal logic
    const state = window.productState || window.productSubmissionState;

    // 2. Pull values from your Test Input fields
    const testL = parseFloat(document.getElementById('test-product-length')?.value) || 1000;
    const testW = parseFloat(document.getElementById('test-product-width')?.value) || 600;
    const testH = parseFloat(document.getElementById('test-product-height')?.value) || 800;
    const testQ = parseFloat(document.getElementById('test-product-qty')?.value) || 1;

    // 3. Prepare Payload (Mapped for Django Evaluator)
    const payload = {
        product_dims: {
            product_length: testL,
            product_width: testW,
            product_height: testH,
            quantity: testQ
        },
        parameters: state.parameters.map(p => ({
            abbr: p.abbr,
            default_value: p.default || p.default_value || 0
        })),
        part_templates: state.parts.map(p => ({
            name: p.name,
            shape_type: p.shape_type || "RECT",
            length_equation: p.geometry.length_eq,
            width_equation: p.geometry.width_eq,
            param1_equation: p.geometry.p1_eq || "0",
            param2_equation: p.geometry.p2_eq || "0",
            quantity_equation: p.geometry.qty_eq || "1"
        }))
    };

    if (payload.part_templates.length === 0) {
        summaryContainer.innerHTML = '<div class="alert alert-warning small">Add parts to see a cut-list preview.</div>';
        return;
    }

    summaryContainer.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm text-primary"></div> Calculating...</div>';

    try {
        const response = await fetch('/modularcalc/api/dryrun/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.CSRF_TOKEN // Using your global token
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
            renderCutListTable(result.preview, {testL, testW, testH});
        } else {
            // Display specific error (like "product_height must be > 100")
            summaryContainer.innerHTML = `<div class="alert alert-danger small"><strong>Calculation Error:</strong> ${result.error}</div>`;
        }
    } catch (e) {
        summaryContainer.innerHTML = `<div class="alert alert-danger small">Network Error: Could not reach the Factory Engine.</div>`;
        console.error("Dry Run Failed:", e);
    }
}

function renderCutListTable(previewData, dims) {
    const container = document.getElementById('cutlist-container');
    const badge = document.getElementById('validation-status-badge');
    
    // Update Badge to Green
    badge.className = "badge rounded-pill bg-success text-white";
    badge.innerHTML = `<i class="bi bi-check-circle-fill"></i> Calculated`;

    let html = `
        <table class="table table-hover table-sm border-0 mb-0">
            <thead class="bg-light sticky-top">
                <tr>
                    <th class="ps-3 py-2 small">PART NAME</th>
                    <th class="py-2 small text-center">LENGTH</th>
                    <th class="py-2 small text-center">WIDTH</th>
                    <th class="py-2 small text-center">QTY</th>
                </tr>
            </thead>
            <tbody>
    `;

    html += previewData.map(item => `
        <tr class="align-middle">
            <td class="ps-3">
                <div class="fw-bold text-dark">${item.name}</div>
                <div class="x-small text-muted">${item.shape_type || 'RECT'}</div>
            </td>
            <td class="text-center font-monospace text-primary fw-bold">${parseFloat(item.length).toFixed(1)}</td>
            <td class="text-center font-monospace text-primary fw-bold">${parseFloat(item.width).toFixed(1)}</td>
            <td class="text-center"><span class="badge bg-light text-dark border">${item.quantity || 1}</span></td>
        </tr>
    `).join('');

    html += `
            </tbody>
        </table>
        <div class="p-2 border-top bg-light x-small text-center text-muted">
            Total Parts: ${previewData.length} | Runtime: ${new Date().toLocaleTimeString()}
        </div>
    `;
    
    container.innerHTML = html;
}