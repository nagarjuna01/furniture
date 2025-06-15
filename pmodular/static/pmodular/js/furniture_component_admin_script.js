// pmodular/js/furniture_component_admin_script.js

(function($) {
    console.log("furniture_component_admin_script.js loaded and running!");

    $(document).ready(function() {
        // Function to toggle readonly state of a formula field based on a checkbox
        function toggleOverrideField(checkbox) {
            var checkboxId = $(checkbox).attr('id');
            var prefixMatch = checkboxId.match(/id_form-\d+-/);
            
            if (prefixMatch) {
                var prefix = prefixMatch[0];
                var formulaFieldName;

                if (checkboxId.endsWith('_use_default_labor_cost')) {
                    formulaFieldName = 'labor_cost_formula';
                } else if (checkboxId.endsWith('_use_default_hardware_cost')) {
                    formulaFieldName = 'hardware_cost_formula';
                } else if (checkboxId.endsWith('_use_default_edge_band_cost')) {
                    formulaFieldName = 'edge_band_cost_formula';
                } else {
                    console.warn("Unrecognized override checkbox ID suffix:", checkboxId);
                    return;
                }

                var formulaField = $('#' + prefix + formulaFieldName); 

                if (formulaField.length) { 
                    if ($(checkbox).is(':checked')) {
                        formulaField.prop('readonly', true);
                        formulaField.val(''); // Clear the value when using default
                        console.log("Checkbox checked, made " + formulaField.attr('id') + " readonly and cleared its value.");
                    } else {
                        formulaField.prop('readonly', false);
                        console.log("Checkbox unchecked, made " + formulaField.attr('id') + " editable.");
                    }
                } else {
                    console.warn("WARNING: Target formula field NOT FOUND for ID:", prefix + formulaFieldName, ". Check HTML structure.");
                }
            } else {
                console.warn("WARNING: Could not extract form prefix from checkbox ID:", checkboxId);
            }
        }

        // --- Event binding and initialization ---

        // Selector for all "Use Module Default" checkboxes
        var overrideCheckboxesSelector = 
            'input[type="checkbox"][id$="_use_default_labor_cost"], ' +
            'input[type="checkbox"][id$="_use_default_hardware_cost"], ' +
            'input[type="checkbox"][id$="_use_default_edge_band_cost"]';

        // 1. Initialize on page load for existing inline rows
        $('.inline-group').each(function(index, group) {
            $(group).find(overrideCheckboxesSelector).each(function() {
                toggleOverrideField(this);
            });
        });

        // 2. Attach change event listener for dynamic interaction
        $(document).on('change', overrideCheckboxesSelector, function() {
            toggleOverrideField(this);
        });

        // 3. Handle dynamically added new inline rows
        $(document).on('formset:added', function(event, row) {
            $(row).find(overrideCheckboxesSelector).each(function() {
                toggleOverrideField(this);
            });
        });
    });
})(django.jQuery);
