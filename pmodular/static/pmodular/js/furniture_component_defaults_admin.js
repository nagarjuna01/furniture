// pmodular/js/furniture_component_defaults_admin.js

(function($) {
    console.log("furniture_component_defaults_admin.js loaded and running!"); // Debugging line

    $(document).ready(function() {
        // Function to toggle readonly state of a formula field based on a checkbox
        function toggleFormulaField(checkbox) {
            var checkboxId = $(checkbox).attr('id');
            // Extract the common prefix (e.g., 'id_form-0-')
            var prefixMatch = checkboxId.match(/id_form-\d+-/);
            
            if (prefixMatch) {
                var prefix = prefixMatch[0];
                var formulaFieldName;

                // Determine the corresponding formula field name based on checkbox ID suffix
                if (checkboxId.endsWith('_use_default_purchase_cost')) {
                    formulaFieldName = 'purchase_cost_per_unit_formula';
                } else if (checkboxId.endsWith('_use_default_sell_price')) {
                    formulaFieldName = 'sell_price_per_unit_formula';
                } else if (checkboxId.endsWith('_use_default_labor_cost')) {
                    formulaFieldName = 'labor_cost_formula';
                } else if (checkboxId.endsWith('_use_default_hardware_cost')) {
                    formulaFieldName = 'hardware_cost_formula';
                } else if (checkboxId.endsWith('_use_default_edge_band_cost')) {
                    formulaFieldName = 'edge_band_cost_formula';
                } else {
                    console.warn("Unrecognized default checkbox ID suffix:", checkboxId);
                    return; // Not a recognized default checkbox
                }

                var formulaFieldId = prefix + formulaFieldName;
                var formulaField = $('#' + formulaFieldId); // Target by exact ID

                if (formulaField.length) { // Ensure the formula field element exists
                    if ($(checkbox).is(':checked')) {
                        formulaField.prop('readonly', true);
                        // console.log("Checkbox checked, making " + formulaFieldId + " readonly."); // More debug
                    } else {
                        formulaField.prop('readonly', false);
                        // console.log("Checkbox unchecked, making " + formulaFieldId + " editable."); // More debug
                    }
                } else {
                    console.warn("Target formula field not found for ID:", formulaFieldId); // Debug if field not found
                }
            }
        }

        // --- Event binding and initialization ---

        // Selector for all "Use Default" checkboxes
        var defaultCheckboxesSelector = 
            'input[type="checkbox"][id$="_use_default_purchase_cost"], ' +
            'input[type="checkbox"][id$="_use_default_sell_price"], ' +
            'input[type="checkbox"][id$="_use_default_labor_cost"], ' +
            'input[type="checkbox"][id$="_use_default_hardware_cost"], ' +
            'input[type="checkbox"][id$="_use_default_edge_band_cost"]';

        // 1. Initialize on page load for existing inline rows
        // Django admin's inlines are often nested within a specific structure.
        // We need to ensure we target the *actual* checkboxes within the forms.
        // The inline-group is a common wrapper.
        $('.inline-group').each(function() {
            $(this).find(defaultCheckboxesSelector).each(function() {
                toggleFormulaField(this);
            });
        });


        // 2. Attach change event listener for dynamic interaction
        $(document).on('change', defaultCheckboxesSelector, function() {
            toggleFormulaField(this);
        });

        // 3. Handle dynamically added new inline rows
        // Django's inlines trigger 'formset:added' event on the document
        $(document).on('formset:added', function(event, row) {
            // 'row' is the new inline row element
            $(row).find(defaultCheckboxesSelector).each(function() {
                toggleFormulaField(this);
            });
        });
    });
})(django.jQuery);
