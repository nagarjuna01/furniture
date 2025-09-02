$(function () {
  function initHRRepeater() {
    const container = '#hrContainer';
    const tplId = '#hrTemplate';
    const itemClass = '.hr-item';

    $('#addHRBtn').click(() => {
      $(container).find('.empty-msg').remove();

      const item = $($(tplId)[0].content.cloneNode(true));
      const $item = $(item);

      const $ruleSelect = $item.find('select[name="hw_requirements[][rule]"]');
      const $customEq = $item.find('input[name="hw_requirements[][custom_equation]"]');
      const $quantity = $item.find('input[name="hw_requirements[][quantity]"]');

      $quantity.on('input', function () {
        const hasQty = !!$(this).val();
        $ruleSelect.prop('disabled', hasQty);
        $customEq.prop('disabled', hasQty);
      });

      $ruleSelect.on('change', function () {
        const ruleSet = !!$(this).val();
        if (ruleSet) {
          $quantity.prop('disabled', true);
        } else if (!$customEq.val()) {
          $quantity.prop('disabled', false);
        }
      });

      $customEq.on('input', function () {
        const eqSet = !!$(this).val();
        if (eqSet) {
          $ruleSelect.prop('disabled', true);
          $quantity.prop('disabled', true);
        } else if (!$ruleSelect.val()) {
          $ruleSelect.prop('disabled', false);
          $quantity.prop('disabled', false);
        }
      });

      $(container).append($item);
    });

    $(container).on('click', '.remove-btn', function () {
      $(this).closest(itemClass).remove();
      if ($(container).find(itemClass).length === 0) {
        $(container).append(`<p class="text-muted empty-msg">No hardware requirements added.</p>`);
      }
    });
  }

  function validateHRInputs() {
    let valid = true;

    $('.hr-item').each(function () {
      $(this).append(`<small class="text-danger">Please fill at least one field.</small>`);  
      const rule = $(this).find('select[name="hw_requirements[][rule]"]').val();
      const eq = $(this).find('input[name="hw_requirements[][custom_equation]"]').val();
      const qty = $(this).find('input[name="hw_requirements[][quantity]"]').val();

      if (!rule && !eq && !qty) {
        valid = false;
        $(this).addClass('border-danger');
      } else {
        $(this).removeClass('border-danger');
      }
    });

    return valid;
  }

  $('#productWizardForm').on('submit', function (e) {
    if (!validateHRInputs()) {
      e.preventDefault();
      alert('Each hardware requirement must have a Rule, Equation, or Quantity.');
    }
  });

  // ✅ Run repeater on load
  initHRRepeater();
});
