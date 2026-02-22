$(document).on("click", ".override-part-btn", function () {
  const partId = $(this).closest(".part-row").data("part-id");

  console.log("Override part", partId);
  $("#override-part-id").val(partId);

  $("#override-material").select2({
    dropdownParent: $("#partOverrideModal"),
    ajax: {
      url: "/materials/api/select/",
      dataType: "json",
      delay: 250,
      data: params => ({ q: params.term }),
      processResults: data => ({
        results: data.results
      })
    }
  });

  $("#partOverrideModal").modal("show");
});
$("#save-part-override").on("click", function () {
  const payload = {
    material: $("#override-material").val(),
    quantity: $("#override-qty").val(),
    rate_override: $("#override-rate").val()
  };

  const partId = $("#override-part-id").val();

  $.ajax({
    url: `/quoting/api/quote-parts/${partId}/`,
    method: "PATCH",
    data: payload
  })
  .done(() => {
    console.log("Override saved");
    $("#partOverrideModal").modal("hide");
    QuoteApp.loadQuote();   // 🔥 recalculated values appear
  })
  .fail(xhr => {
    console.error("Override failed", xhr.responseText);
    alert("Override failed");
  });
});
