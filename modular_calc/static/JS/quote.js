let CURRENT_QUOTE_ID = null;

function openQuoteModal(quoteId) {
    CURRENT_QUOTE_ID = quoteId;
    $('#quote-products').html('');
    $('#btn-approve').addClass('d-none');

    $.ajax({
        url: `/api/quotes/${quoteId}/`,
        method: 'GET',
        success: function (res) {
            console.log("Quote loaded:", res);

            $('#q-customer').text(res.customer_name || '-');
            $('#q-status').text(res.status || 'draft');

            renderQuoteProducts(res.products);

            $('#quoteModal').modal('show');
        },
        error: function (xhr) {
            console.error(xhr.responseText);
            alert("Failed to load quote");
        }
    });
}
function renderQuoteProducts(products) {
    let html = '';

    products.forEach(p => {
        html += `
        <div class="card mb-3">
          <div class="card-header d-flex justify-content-between">
            <strong>${p.product_name}</strong>
            <span>Qty: ${p.quantity}</span>
          </div>

          <div class="card-body">
            <div class="row mb-2">
              <div class="col-md-3">L: ${p.length_mm} mm</div>
              <div class="col-md-3">W: ${p.width_mm} mm</div>
              <div class="col-md-3">H: ${p.height_mm} mm</div>
              <div class="col-md-3">
                Validated: ${p.validated ? '✅' : '❌'}
              </div>
            </div>

            <div>
              <strong>Parts:</strong>
              <div id="parts-${p.id}">
                ${p.parts && p.parts.length ? renderParts(p.parts) : '<em>Not expanded</em>'}
              </div>
            </div>
          </div>
        </div>`;
    });

    $('#quote-products').html(html);
}
function renderParts(parts) {
    let rows = `
    <table class="table table-sm table-bordered">
      <thead>
        <tr>
          <th>Part</th>
          <th>Size</th>
          <th>Material</th>
          <th>Qty</th>
          <th>Total Cost</th>
        </tr>
      </thead>
      <tbody>`;

    parts.forEach(pt => {
        rows += `
        <tr>
          <td>${pt.part_name}</td>
          <td>${pt.length_mm} × ${pt.width_mm}</td>
          <td>${pt.material_name || '-'}</td>
          <td>${pt.part_qty}</td>
          <td>₹${pt.total_cost || 0}</td>
        </tr>`;
    });

    rows += '</tbody></table>';
    return rows;
}
$('#btn-expand').on('click', function () {
    if (!CURRENT_QUOTE_ID) return;

    $(this).prop('disabled', true).text('Expanding...');

    $.ajax({
        url: `/api/quote-products/${CURRENT_QUOTE_ID}/expand/`,
        method: 'POST',
        success: function (res) {
            console.log("Expanded:", res);
            alert(`Parts generated: ${res.parts_generated}`);
            location.reload(); // reload to fetch expanded parts
        },
        error: function (xhr) {
            console.error(xhr.responseText);
            alert("Expand failed");
        },
        complete: function () {
            $('#btn-expand').prop('disabled', false).text('Expand Parts');
        }
    });
});
$('#btn-approve').on('click', function () {
    if (!CURRENT_QUOTE_ID) return;

    if (!confirm("Approve this quote for production?")) return;

    $.ajax({
        url: `/api/quotes/${CURRENT_QUOTE_ID}/approve/`,
        method: 'POST',
        success: function () {
            alert("Quote approved and locked");
            $('#quoteModal').modal('hide');
            location.reload();
        },
        error: function (xhr) {
            console.error(xhr.responseText);
            alert("Approval failed");
        }
    });
});
