// ----------------------------
// EDGEBAND MODAL
// ----------------------------
window.openEdgebandModal = function() {
    // Reset filters
    document.querySelectorAll('.filter-depth, .filter-name, .filter-thickness, .filter-brand')
        .forEach(select => select.value = "");

    ['top','right','bottom','left'].forEach(side => renderEdgebandSide(side));
    renderSelectedEdgebands();
    new bootstrap.Modal(document.getElementById('edgebandModal')).show();
};

function initEdgebandFilters() {
    ['top','right','bottom','left'].forEach(side => {
        ['depth','name','thickness','brand'].forEach(field => fillFilterSelect(side, field));
    });

    // Attach change events to all filters
    document.querySelectorAll('.filter-depth, .filter-name, .filter-thickness, .filter-brand')
        .forEach(sel => sel.addEventListener('change', e => {
            const side = e.target.dataset.side;
            renderEdgebandSide(side);
            // Re-populate all dropdowns for cascading effect
            ['depth','name','thickness','brand'].forEach(field => fillFilterSelect(side, field));
        }));
}

function fillFilterSelect(side, field) {
    const select = document.querySelector(`.filter-${field}[data-side="${side}"]`);
    if (!select) return;

    // Get current selected values for other fields
    const currentFilters = {
        depth: document.querySelector(`.filter-depth[data-side="${side}"]`)?.value,
        name: document.querySelector(`.filter-name[data-side="${side}"]`)?.value,
        thickness: document.querySelector(`.filter-thickness[data-side="${side}"]`)?.value,
        brand: document.querySelector(`.filter-brand[data-side="${side}"]`)?.value
    };

    // Build filtered dataset excluding the field we are populating
    const filtered = allData.edgebands.filter(e => {
        return (!currentFilters.depth || field === 'depth' ? true : e.edgeband_name?.depth === currentFilters.depth) &&
               (!currentFilters.name || field === 'name' ? true : e.edgeband_name?.name === currentFilters.name) &&
               (!currentFilters.thickness || field === 'thickness' ? true : e.e_thickness === currentFilters.thickness) &&
               (!currentFilters.brand || field === 'brand' ? true : e.brand?.name === currentFilters.brand);
    });

    // Get unique values for this field
    let values = [];
    if(field === 'depth') values = [...new Set(filtered.map(e => e.edgeband_name?.depth).filter(Boolean))];
    else if(field === 'name') values = [...new Set(filtered.map(e => e.edgeband_name?.name).filter(Boolean))];
    else if(field === 'thickness') values = [...new Set(filtered.map(e => e.e_thickness).filter(Boolean))];
    else if(field === 'brand') values = [...new Set(filtered.map(e => e.brand?.name).filter(Boolean))];

    // Rebuild select options
    const prevValue = select.value;
    select.innerHTML = `<option value="">All</option>`;
    values.forEach(v => select.appendChild(new Option(v,v)));
    if(values.includes(prevValue)) select.value = prevValue; // keep current selection if still valid
}

// Render table for one side
function renderEdgebandSide(side) {
    const tbody = document.getElementById(`edgeband-body-${side}`);
    if(!tbody) return;

    const depth = document.querySelector(`.filter-depth[data-side="${side}"]`)?.value;
    const name  = document.querySelector(`.filter-name[data-side="${side}"]`)?.value;
    const thickness = document.querySelector(`.filter-thickness[data-side="${side}"]`)?.value;
    const brand = document.querySelector(`.filter-brand[data-side="${side}"]`)?.value;

    tbody.innerHTML = '';

    const filtered = allData.edgebands.filter(e =>
        (!depth || e.edgeband_name?.depth === depth) &&
        (!name || e.edgeband_name?.name === name) &&
        (!thickness || e.e_thickness === thickness) &&
        (!brand || e.brand?.name === brand)
    );

    filtered.forEach(e => {
        const tr = document.createElement('tr');
        const isChecked = selected.edgebands[side].whitelist.some(w=>w.id===e.id);
        const isDefault = selected.edgebands[side].default===e.id;
        tr.innerHTML = `
            <td>${e.display_name}</td>
            <td><input type="checkbox" class="edgeband-whitelist" data-side="${side}" data-id="${e.id}" ${isChecked?'checked':''}></td>
            <td><input type="radio" name="edgeband-default-${side}" class="edgeband-default" data-side="${side}" data-id="${e.id}" ${isDefault?'checked':''}></td>
        `;
        tbody.appendChild(tr);
    });
}

// Handle checkboxes & radio buttons
document.addEventListener('change', e=>{
    const side = e.target.dataset.side;
    const id = parseInt(e.target.dataset.id);
    if(!side||!id) return;

    if(e.target.classList.contains('edgeband-whitelist')) {
        if(e.target.checked){
            const ed = allData.edgebands.find(ed => ed.id===id);
            if(!selected.edgebands[side].whitelist.some(w=>w.id===id))
                selected.edgebands[side].whitelist.push(ed);
        } else {
            selected.edgebands[side].whitelist = selected.edgebands[side].whitelist.filter(w=>w.id!==id);
            if(selected.edgebands[side].default===id) selected.edgebands[side].default=null;
        }
    }

    if(e.target.classList.contains('edgeband-default')){
        selected.edgebands[side].default = id;
        if(!selected.edgebands[side].whitelist.some(w=>w.id===id)){
            const ed = allData.edgebands.find(ed => ed.id===id);
            selected.edgebands[side].whitelist.push(ed);
        }
    }

    renderSelectedEdgebands();
});

// Display selected summary
function renderSelectedEdgebands(){
    const container = document.getElementById('selected-edgebands');
    container.innerHTML='';
    ['top','right','bottom','left'].forEach(side=>{
        const sideDiv=document.createElement('div');
        const wl = selected.edgebands[side].whitelist.map(w=>w.display_name).join(', ');
        const def = selected.edgebands[side].default?allData.edgebands.find(e=>e.id===selected.edgebands[side].default)?.display_name:'(None)';
        sideDiv.innerHTML=`<strong>${side.toUpperCase()}</strong> → Whitelist: ${wl||'(None)'}, Default: ${def}`;
        container.appendChild(sideDiv);
    });
}


// Save button
document.getElementById('save-edgeband-btn').addEventListener('click',()=>{
    console.log("Selected Edgebands:", selected.edgebands);
    document.dispatchEvent(new CustomEvent("edgebandsSaved", { detail: selected.edgebands }));
    bootstrap.Modal.getInstance(document.getElementById('edgebandModal')).hide();
});

