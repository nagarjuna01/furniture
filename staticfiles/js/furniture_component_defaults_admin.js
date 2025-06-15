// pmodular/js/furniture_component_defaults_admin.js

(function($) {
    $(document).ready(function() {
        // Function to toggle readonly state of a formula field
        function toggleFormulaField(checkbox) {
            var formulaField = $(checkbox).closest('.form-row').find('textarea'); // Find the textarea within the same row/group
            if ($(checkbox).is(':checked')) {
                formulaField.prop('readonly', true);
            } else {
                formulaField.prop('readonly', false);
            }
        }

        // Initialize on page load for existing inline rows
        $('.inline-related').each(function() {
            var inlineTable = $(this);
            inlineTable.find('tbody tr:not(.empty-form)').each(function() {
                // Find all checkboxes for default formulas within this row
                $(this).find('input[type="checkbox"][id$="_use_default_purchase_cost"], ' +
                             'input[type="checkbox"][id$="_use_default_sell_price"], ' +
                             'input[type="checkbox"][id$="_use_default_labor_cost"], ' +
                             'input[type="checkbox"][id$="_use_default_hardware_cost"], ' +
                             'input[type="checkbox"][id$="_use_default_edge_band_cost"]').each(function() {
                    toggleFormulaField(this);
                });
            });
        });

        // Attach change event listener to all "Use Default" checkboxes
        $(document).on('change', 'input[type="checkbox"][id$="_use_default_purchase_cost"], ' +
                                 'input[type="checkbox"][id$="_use_default_sell_price"], ' +
                                 'input[type="checkbox"][id$="_use_default_labor_cost"], ' +
                                 'input[type="checkbox"][id$="_use_default_hardware_cost"], ' +
                                 'input[type="checkbox"][id$="_use_default_edge_band_cost"]', function() {
            toggleFormulaField(this);
        });

        // Handle dynamically added new inline rows
        $(document).on('formset:added', function(event, row) {
            $(row).find('input[type="checkbox"][id$="_use_default_purchase_cost"], ' +
                         'input[type="checkbox"][id$="_use_default_sell_price"], ' +
                         'input[type="checkbox"][id$="_use_default_labor_cost"], ' +
                         'input[type="checkbox"][id$="_use_default_hardware_cost"], ' +
                         'input[type="checkbox"][id$="_use_default_edge_band_cost"]').each(function() {
                toggleFormulaField(this);
            });
        });
    });
})(django.jQuery);
