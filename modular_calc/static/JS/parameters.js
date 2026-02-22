if (!window.productSubmissionState) {
    window.productSubmissionState = { parameters: [], parts: [] };
}
document.addEventListener('DOMContentLoaded', () => {
    const saveBtn = document.getElementById('save-param-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', addParameter);
    }
});
function addParameter() {
    const nameInput = document.getElementById('param-name');
    const abbrInput = document.getElementById('param-abbr');
    const defaultInput = document.getElementById('param-default');
    const descInput = document.getElementById('param-desc');
    const param = {
        name: nameInput.value.trim(),
        abbreviation: abbrInput.value.trim().toUpperCase().replace(/\s+/g, '_'), 
        default_value: parseFloat(defaultInput.value) || 0,
        description: descInput.value.trim()
    };
    if (!param.name || !param.abbreviation) {
        // Use a custom message box or console since alert() is restricted
        console.warn("Please provide both a Name and an Abbreviation.");
        return;
    }
    // FIX: Check duplicates against .abbreviation
    const isDuplicate = window.productSubmissionState.parameters.some(
        p => p.abbreviation.toUpperCase() === param.abbreviation
    );

    if (isDuplicate) {
        console.warn(`The variable '${param.abbreviation}' is already defined.`);
        return;
    }
    window.productSubmissionState.parameters.push(param);
    [nameInput, abbrInput, defaultInput, descInput].forEach(i => i.value = '');
    renderParameterTable();
}

function renderParameterTable() {
    const tbody = document.getElementById('parameter-body');
    if (!tbody) return;

    if (!window.productSubmissionState.parameters || window.productSubmissionState.parameters.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-2">No parameters defined.</td></tr>';
        return;
    }

    tbody.innerHTML = window.productSubmissionState.parameters.map((p, index) => `
    <tr class="small align-middle">
        <td>${p.name}</td>
        <td><code class="fw-bold text-primary">${p.abbreviation}</code></td>
        <td>${p.default_value}</td>
        <td class="text-muted small">${p.description || '-'}</td>
        <td class="text-center">
            <button type="button" 
                    class="btn btn-sm btn-danger d-flex align-items-center justify-content-center" 
                    style="min-width: 30px; height: 30px;"
                    onclick="window.deleteParameter(${index})">
                <i class="bi bi-trash"></i>
                <span class="d-none d-md-inline ms-1" style="font-size: 10px;">Delete</span>
            </button>
        </td>
    </tr>
`).join('');
}

window.deleteParameter = function(index) {
    window.productSubmissionState.parameters.splice(index, 1);
    renderParameterTable();
};