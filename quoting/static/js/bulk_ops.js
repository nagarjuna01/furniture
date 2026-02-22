const BulkOps = {
  selected: new Set(),

  syncUI() {
    $("#bulk-selected-count").text(this.selected.size);
    $("#bulk-action-bar").toggleClass(
      "d-none",
      this.selected.size === 0
    );
  },

  toggle(id, checked) {
    checked ? this.selected.add(id) : this.selected.delete(id);
    this.syncUI();
  },

  clear() {
    this.selected.clear();
    $(".bulk-product-checkbox").prop("checked", false);
    this.syncUI();
  },
};

$(document).on("change", ".bulk-product-checkbox", function () {
  BulkOps.toggle($(this).val(), this.checked);
});
function runBulkAction(action) {
  const ids = Array.from(BulkOps.selected);

  if (!ids.length) return;

  console.log("Bulk action", action, ids);

  $.ajax({
    url: `/quoting/api/quote-products/${action}/`,
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({ product_ids: ids }),
  })
  .done(() => {
    alert(`${action} completed`);
    BulkOps.clear();
    QuoteApp.loadQuote();
  })
  .fail(xhr => {
    console.error("Bulk action failed", xhr.responseText);
    alert("Some items could not be processed");
  });
}

$("#bulk-expand-btn").on("click", () => runBulkAction("bulk_expand"));
$("#bulk-freeze-btn").on("click", () => runBulkAction("bulk_freeze"));
$("#bulk-recalc-btn").on("click", () => runBulkAction("bulk_recalc"));

function loadRevisions(quoteId) {
  $.get(`/quoting/api/quote-revisions/?quote=${quoteId}`, data => {
    const list = $("#revision-list").empty();

    data.forEach(r => {
      list.append(`
        <li class="list-group-item d-flex justify-content-between">
          Revision ${r.revision_no}
          <button class="btn btn-sm btn-outline-info"
                  onclick="viewDiff(${r.id})">
            View Diff
          </button>
        </li>
      `);
    });
  });
}