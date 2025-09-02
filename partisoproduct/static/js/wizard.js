function generateUUID() {
  return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
  );
}

// On load or form reset
if (!localStorage.getItem('modular_uuid')) {
  const uuid = generateUUID();
  localStorage.setItem('modular_uuid', uuid);
  $('#productUUID').val(uuid);
} else {
  $('#productUUID').val(localStorage.getItem('modular_uuid'));
}

  const STEPS = ['step-1', 'step-2', 'step-3', 'step-4', 'step-5'];
  let currentIndex = 0;
  const LOCAL_CACHE_KEY = 'modular_wizard_draft';
  const CURRENT_KEY = 'modular_wizard_current';
  const cached = localStorage.getItem(CURRENT_KEY);
  if (cached) {
    const {data} = JSON.parse(cached);
    for (const k in data) {
      const el = $(`[name="${k}"]`);
      if (el.length) el.val(data[k]);
    }
    $('#productNameInput').val(JSON.parse(cached).name);
    localStorage.removeItem(CURRENT_KEY);  // Optionally delete original snapshot
  }
$(function () {

  function isEditMode() {
  return Boolean($('#productId').val());
}
  function showStep(idx) {
    $('.form-step').addClass('d-none');
    $(`#${STEPS[idx]}`).removeClass('d-none');
    $('#currentStep').val(idx + 1);
    currentIndex = idx;
    $('html, body').scrollTop(0);
  }

  // Material Options Cache
  let MATERIAL_OPTIONS = [];

  function loadMaterialOptions() {
    console.log("⏳ Starting material load...");

    return $.getJSON('/material/v1/woodens/')
      .done(res => {
        MATERIAL_OPTIONS = res.results.map(m => {
          const category = m.material_type?.category?.name || 'Unknown Category';
          const type = m.material_type?.name || 'Unknown Type';
          const model = m.material_model?.name || 'Unknown Model';
          const brand = m.brand?.name || 'Unknown Brand';
          const name = m.name || 'Unnamed Material';

          return {
            id: m.id,
            name: `${category} > ${type} > ${model} > ${brand} - ${name}`,
            compatible_edgebands: m.compatible_edgebands || []
          };
        });
})
      .fail(err => {
        console.error("❌ Failed to load materials", err);
        MATERIAL_OPTIONS = [];
      });
  }

  function collectFormData() {
    const formData = {};
    $('#productWizardForm').serializeArray().forEach(({ name, value }) => {
      if (!formData[name]) {
        formData[name] = value;
      } else if (Array.isArray(formData[name])) {
        formData[name].push(value);
      } else {
        formData[name] = [formData[name], value];
      }
    });
    return formData;
  }

  function saveToLocalCache() {
    const cache = {
      data: collectFormData(),
      timestamp: new Date().toISOString()
    };
    localStorage.setItem(LOCAL_CACHE_KEY, JSON.stringify(cache));
  }

  function loadFromLocalCache() {
    const cached = localStorage.getItem(LOCAL_CACHE_KEY);
    if (!cached) return;

    try {
      const { data } = JSON.parse(cached);
      for (let key in data) {
        const field = $(`[name="${key}"]`);
        if (field.length) {
          field.val(data[key]);
        }
      }
    } catch (e) {
      console.warn('Draft restore failed:', e);
    }
  }

  function ajaxAutoSave(callback) {
    const form = $('#productWizardForm')[0];
    const fd = new FormData(form);
    fd.append('save_step', currentIndex + 1);

    $.ajax({
      url: '/partiso/api/products/autosave/',
      method: 'POST',
      headers: { 'X-CSRFToken': fd.get('csrfmiddlewaretoken') },
      data: fd,
      processData: false,
      contentType: false
    }).done(res => {
      saveToLocalCache();
      if (callback) callback();
    }).fail(err => {
      console.error("Auto-save failed", err);
      alert("Error auto-saving.");
    });
  }

  function ajaxFinalSubmit(action) {
    const form = $('#productWizardForm')[0];
    const fd = new FormData(form);
    fd.append('action', action);
    fd.append('save_step', currentIndex + 1);

    $.ajax({
      url: '/partiso/api/products/final-submit/',
      method: 'POST',
      headers: { 'X-CSRFToken': fd.get('csrfmiddlewaretoken') },
      data: fd,
      processData: false,
      contentType: false
    }).done(res => {
      alert(`Product ${action}ed successfully.`);
      $('#productId').val(res.id);
      localStorage.removeItem(LOCAL_CACHE_KEY);
    }).fail(err => {
      console.error("Final submit failed", err);
      alert("Form submission error.");
    });
  }

  // Debounce helper so evaluate API doesn't get spammed on quick input changes
  function debounce(fn, delay) {
    let timer = null;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  // === Modular parts evaluation call ===
  function evaluateModularParts() {
    const csrfToken = $('[name="csrfmiddlewaretoken"]').val();
    // Prepare parts array
    const parts = [];
    $('#partsContainer .part-item').each(function () {
      const part = $(this);
      parts.push({
        part_length_equation: part.find('input[name="parts[][part_length_equation]"]').val() || '',
        part_width_equation: part.find('input[name="parts[][part_width_equation]"]').val() || '',
        part_qty_equation: part.find('input[name="parts[][part_qty_equation]"]').val() || '',
        part_material: part.find('select[name="parts[][part_material]"]').val() || null,
        grain_direction: part.find('select[name="parts[][grain_direction]"]').val() || null,
        edge_top: part.find('select[name="parts[][edge_top]"]').val() || null,
        edge_bottom: part.find('select[name="parts[][edge_bottom]"]').val() || null,
        edge_left: part.find('select[name="parts[][edge_left]"]').val() || null,
        edge_right: part.find('select[name="parts[][edge_right]"]').val() || null,
      });
    });

    // Prepare product parameters array
    const product_parameters = [];
    $('#parametersContainer .parameter-item').each(function () {
      const param = $(this);
      product_parameters.push({
        name: param.find('input[name="parameters[][name]"]').val() || '',
        value: param.find('input[name="parameters[][value]"]').val() || ''
      });
    });

    $.ajax({
      url: '/partiso/api/modular/evaluate/',
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
      contentType: 'application/json',
      data: JSON.stringify({
        parts,
        product_parameters
      }),
      success: function (response) {
        console.log('Evaluation response:', response);
        
      },
      error: function (xhr) {
        console.error('Evaluation API error:', xhr.responseText);
        alert('Error evaluating parts. Please check your inputs.');
      }
    });
  }
  const debouncedEvaluate = debounce(evaluateModularParts, 500);
  if (isEditMode()) debouncedEvaluate();

  // Navigation buttons
  $(document).on('click', '[data-next-step]', function () {
    const nextStep = parseInt(this.dataset.nextStep) - 1;
     ajaxAutoSave(() => showStep(nextStep));
  });

  $(document).on('click', '[data-prev-step]', function () {
    showStep(parseInt(this.dataset.prevStep) - 1);
  });

  $('#productWizardForm').on('submit', function (e) {
    e.preventDefault();
    const action = $(document.activeElement).val(); // e.g. "draft" or "publish"
    if (action === 'draft') {
    ajaxSaveDraft();
  } else if (action === 'publish') {
    evaluateModularParts();
    ajaxFinalSubmit(action);
  }
});

  // Generic repeater (for parameters, rules, etc.)
  function repeater(addBtn, container, tplId, itemClass) {
    $(addBtn).click(() => {
      $(container).find('.empty-msg').remove();
      const item = $($(tplId)[0].content.cloneNode(true));
      $(container).append(item);

      // After adding a parameter or rule, re-evaluate
      if(container === '#parametersContainer' && isEditMode()){
  debouncedEvaluate();
}
    });

    $(container).on('click', '.remove-btn', function () {
      $(this).closest(itemClass).remove();
      if ($(container).find(itemClass).length === 0) {
        $(container).append(`<p class="text-muted empty-msg">No items added.</p>`);
      }
     
    });

   
  }

  // ✅ Custom Part Repeater — inject materials
  function initPartRepeater() {
    $('#addPartBtn').click(() => {
      $('#partsContainer .empty-msg').remove();

      // Clone part template
      const item = $($('#partTemplate')[0].content.cloneNode(true));
      const part = $(item); // Scoped wrapper

      // 🔁 Populate material dropdown
      const matSelect = part.find('select[name="parts[][part_material]"]');
      MATERIAL_OPTIONS.forEach(opt => {
        matSelect.append(`<option value="${opt.id}">${opt.name}</option>`);
      });

      // 🔄 On material change, update edge band dropdowns and evaluate
      matSelect.on('change', function () {
        const selectedId = parseInt($(this).val());
        const selectedMaterial = MATERIAL_OPTIONS.find(m => m.id === selectedId);

        const edgeOptions = (selectedMaterial && Array.isArray(selectedMaterial.compatible_edgebands))
          ? selectedMaterial.compatible_edgebands
          : [];

        

        // 🧩 Scope to the current .part-item
        const currentPart = $(this).closest('.part-item');

        const edgeFields = {
          top: currentPart.find('select[name="parts[][edge_top]"]'),
          bottom: currentPart.find('select[name="parts[][edge_bottom]"]'),
          left: currentPart.find('select[name="parts[][edge_left]"]'),
          right: currentPart.find('select[name="parts[][edge_right]"]'),
        };

        // 🔁 Repopulate all edge band dropdowns
        Object.values(edgeFields).forEach(select => {
          select.empty().append(`<option value="">Select Edge</option>`);
          edgeOptions.forEach(e => {
            const name = e.display_name || e.name;
            select.append(`<option value="${e.id}">${name}</option>`);
          });
        });

        // Evaluate after material change
        if (isEditMode()) debouncedEvaluate();
      });

      // Also evaluate when any part grain or dimension field changes
      part.on('input change', 'input, select', debouncedEvaluate);

      // Append cloned part card
      $('#partsContainer').append(part);

      // Evaluate after adding a part
      debouncedEvaluate();
    });

    // ❌ Remove part and evaluate
    $('#partsContainer').on('click', '.remove-btn', function () {
      $(this).closest('.part-item').remove();
      if ($('#partsContainer .part-item').length === 0) {
        $('#partsContainer').append(`<p class="text-muted empty-msg">No parts added.</p>`);
      }
      debouncedEvaluate();
    });
  }

  const grainMap = {
    "0": "none",
    "1": "horizontal",
    "2": "vertical"
  };

  // Call this when either panel or part grain changes
  function validateGrainMatch(panelGrainCode, partGrain, $targetSelect = null) {
    const panelGrain = grainMap[panelGrainCode];

    // Allow 'none' in either case
    if (panelGrain === "none" || partGrain === "none") {
      return true;
    }

    const valid = panelGrain === partGrain;

    if (!valid && $targetSelect) {
      $targetSelect.addClass('is-invalid');
      $targetSelect.after(`<div class="invalid-feedback grain-error">Part grain (${partGrain}) doesn't match panel grain (${panelGrain})</div>`);
    } else {
      $targetSelect?.removeClass('is-invalid');
      $('.grain-error').remove();
    }

    return valid;
  }
  $('.grain-select').on('change', function () {
    const $partGrainSelect = $(this);
    const partGrain = $partGrainSelect.val();

    const panelGrain = $('#panel_material option:selected').data('grain'); // e.g. "2"

    validateGrainMatch(panelGrain, partGrain, $partGrainSelect);

    if (isEditMode()) debouncedEvaluate();
  });

  $('#panel_material').on('change', function () {
    const panelGrain = $(this).find(':selected').data('grain');

    // Re-validate all parts (if you're editing multiple parts)
    $('.grain-select').each(function () {
      const partGrain = $(this).val();
      validateGrainMatch(panelGrain, partGrain, $(this));
    });

    if (isEditMode()) debouncedEvaluate();
  });
$('#addNewBtn').click(() => {
  $('#productWizardForm')[0].reset();
  $('#productId').val('');
  localStorage.removeItem(LOCAL_CACHE_KEY);
  showStep(0);
});

  function initHWRequirementToggle($container) {
    function resetSiblings($el, selector) {
      $el.closest('.hr-item').find(selector).not($el).each(function () {
        $(this).val('').prop('disabled', true);
      });
    }

    $container.on('input change', '.rule-select, .custom-equation, .quantity', function () {
      const $this = $(this);
      const type = $this.data('type');

      // Enable this input
      $this.prop('disabled', false);

      // Disable siblings
      resetSiblings($this, '.rule-select, .custom-equation, .quantity');
    });

    $container.on('blur', '.rule-select, .custom-equation, .quantity', function () {
      const $this = $(this);
      if (!$this.val()) {
        $this.closest('.hr-item').find('.rule-select, .custom-equation, .quantity').prop('disabled', false);
      }
    });
  }

  // Init all repeaters
  repeater('#addParamBtn', '#parametersContainer', '#parameterTemplate', '.parameter-item');
  repeater('#addRuleBtn', '#rulesContainer', '#ruleTemplate', '.rule-item');
  repeater('#addHRBtn', '#hrContainer', '#hrTemplate', '.hr-item');
  initHWRequirementToggle($('#hrContainer'));

  // 🚀 Load material options before enabling part repeater
  loadMaterialOptions().then(() => {
    initPartRepeater();
  });
if (isEditMode()) {
  const productId = $('#productId').val();
  loadExistingProductData(productId); // You can define this function right after this block
}
  // Auto-save every 30s
  setInterval(() => {
    saveToLocalCache();
    console.debug('Auto-saved draft to localStorage');
  }, 30000);

  

  showStep(0);
});
function ajaxSaveDraft() {
  const form = $('#productWizardForm')[0];
  const fd = new FormData(form);

  const productId = $('#productId').val();
  if (productId) {
    fd.append('id', productId);
  }

  $.ajax({
    url: '/partiso/api/modular1/save-draft/',
    method: 'POST',
    
    data: fd,
    processData: false,
    contentType: false
  }).done(res => {
    alert("✅ Draft saved.");
    if (res.id) {
      $('#productId').val(res.id); // Set form ID if it's new
    }
    saveToLocalCache();
  }).fail(err => {
    console.error("❌ Draft save failed", err);
    alert("Failed to save draft.");
  });
}
function loadExistingProductData(productId) {
  $.getJSON(`/partiso/api/products/${productId}/`)
    .done(data => {
      // 🔹 Step 1
      $('[name="name"]').val(data.name);
      $('[name="length_mm"]').val(data.length_mm);
      $('[name="width_mm"]').val(data.width_mm);
      $('[name="height_mm"]').val(data.height_mm);
      $('[name="product_validation_expression"]').val(data.product_validation_expression);

      // 🔹 Step 2: Parameters
      $('#parametersContainer').empty();
      data.parameters?.forEach(param => {
        const $item = $($('#parameterTemplate')[0].content.cloneNode(true));
        $item.find('[name="parameters[][name]"]').val(param.name);
        $item.find('[name="parameters[][abbreviation]"]').val(param.abbreviation);
        $item.find('[name="parameters[][value]"]').val(param.value);
        $('#parametersContainer').append($item);
      });

      // 🔹 Step 3: Parts
      $('#partsContainer').empty();
      data.parts?.forEach(part => {
        const $item = $($('#partTemplate')[0].content.cloneNode(true));
        const wrapper = $item;

        wrapper.find('[name="parts[][name]"]').val(part.name);
        wrapper.find('[name="parts[][length_equation]"]').val(part.length_equation);
        wrapper.find('[name="parts[][width_equation]"]').val(part.width_equation);
        wrapper.find('[name="parts[][qty_equation]"]').val(part.qty_equation);
        wrapper.find('[name="parts[][part_material]"]').val(part.part_material);

        wrapper.find('[name="parts[][edge_top]"]').val(part.edge_top);
        wrapper.find('[name="parts[][edge_bottom]"]').val(part.edge_bottom);
        wrapper.find('[name="parts[][edge_left]"]').val(part.edge_left);
        wrapper.find('[name="parts[][edge_right]"]').val(part.edge_right);

        wrapper.find('[name="parts[][grooving_cost]"]').val(part.grooving_cost);
        wrapper.find('[name="parts[][wastage_multiplier]"]').val(part.wastage_multiplier);
        wrapper.find('[name="parts[][shape]"]').val(part.shape);
        wrapper.find('[name="parts[][grain_direction]"]').val(part.grain_direction);

        $('#partsContainer').append(wrapper);
      });

      // 🔹 Step 4: Hardware Rules
      $('#rulesContainer').empty();
      data.hardware_rules?.forEach(rule => {
        const $item = $($('#ruleTemplate')[0].content.cloneNode(true));
        $item.find('[name="hardware_rules[][name]"]').val(rule.name);
        $item.find('[name="hardware_rules[][equation]"]').val(rule.equation);
        $('#rulesContainer').append($item);
      });

      // 🔹 Step 5: Hardware Requirements
      $('#hrContainer').empty();
      data.hw_requirements?.forEach(req => {
        const $item = $($('#hrTemplate')[0].content.cloneNode(true));
        $item.find('[name="hw_requirements[][hardware]"]').val(req.hardware);
        $item.find('[name="hw_requirements[][rule]"]').val(req.rule);
        $item.find('[name="hw_requirements[][custom_equation]"]').val(req.custom_equation);
        $item.find('[name="hw_requirements[][quantity]"]').val(req.quantity);
        $('#hrContainer').append($item);
      });

      // Trigger evaluation after full load
      debouncedEvaluate();
    })
    .fail(err => {
      console.error("❌ Failed to load product", err);
      alert("Error loading existing product.");
    });
}
