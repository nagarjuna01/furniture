$(document).on("click", ".override-hardware-btn", function () {
  const row = $(this).closest(".hardware-row");
  const hardwareId = row.data("hardware-id");

  console.log("Override hardware", hardwareId);

  $("#override-hardware-id").val(hardwareId);
  $("#override-hardware-qty").val("");
  $("#override-hardware-rate").val("");

  $("#hardwareOverrideModal").modal("show");
});
$("#save-hardware-override").on("click", function () {
  const hardwareId = $("#override-hardware-id").val();

  const payload = {
    quantity: $("#override-hardware-qty").val(),
    rate_override: $("#override-hardware-rate").val(),
  };

  $.ajax({
    url: `/quoting/api/quote-hardware/${hardwareId}/`,
    method: "PATCH",
    data: payload,
  })
  .done(() => {
    console.log("Hardware override saved");
    $("#hardwareOverrideModal").modal("hide");
    QuoteApp.loadQuote(); // 🔁 full recalculation visible
  })
  .fail(xhr => {
    console.error("Hardware override failed", xhr.responseText);
    alert("Override failed");
  });
});