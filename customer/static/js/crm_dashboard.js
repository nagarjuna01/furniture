// crm_dashboard.js
// Place under static/js/crm_dashboard.js
// Uses jQuery + Bootstrap 5 + toastr (toastr already included in base_crm)

(function(){
  console.log('[crm] dashboard init');

  // Basic config: entity -> api path and columns renderers
  const API_BASE = '/customerCRM/api/';
  const ENTITIES = {
    clients: { url: 'clients/', table: '#clients-table', pag: '#clients-pagination' },
    leads: { url: 'leads/', table: '#leads-table', pag: '#leads-pagination' },
    opportunities: { url: 'opportunities/', table: '#opps-table', pag: '#opps-pagination' },
    supporttickets: { url: 'supporttickets/', table: '#tickets-table', pag: '#tickets-pagination' },
    interactions: { url: 'interactions/', table: '#interactions-table', pag: '#interactions-pagination' },
  };

  // helper: CSRF token
  function getCSRF() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
  }

  // helper: authorization header (JWT if present)
  function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    if (token) return { 'Authorization': 'Bearer ' + token };
    return {};
  }

  // Ajax helpers with debug logging
  function ajax(opts) {
    opts.headers = Object.assign({}, opts.headers || {}, getAuthHeaders(), {'X-CSRFToken': getCSRF()});
    console.log('[crm][ajax]', opts.type || 'GET', opts.url, opts.data || '');
    return $.ajax(opts).fail(function(jqXHR, textStatus, errorThrown){
      console.error('[crm][ajax][fail]', opts.url, textStatus, errorThrown, jqXHR.responseText);
      if(jqXHR.responseJSON && jqXHR.responseJSON.detail) {
        toastr.error(jqXHR.responseJSON.detail);
      } else if (jqXHR.responseText) {
        toastr.error(jqXHR.responseText);
      } else {
        toastr.error('Request failed: ' + textStatus);
      }
    });
  }

  // Fetch KPIs
  function fetchKPIs() {
    // We can parallel fetch counts from list endpoints (Limit requests to 1 item to get count via length header isn't standard).
    // Instead, use ?limit=1 and inspect 'count' from DRF paginated response.
    $.when(
      ajax({ url: API_BASE + ENTITIES.clients.url + '?limit=1' }),
      ajax({ url: API_BASE + ENTITIES.leads.url + '?limit=1' }),
      ajax({ url: API_BASE + ENTITIES.opportunities.url + '?limit=1' }),
      ajax({ url: API_BASE + ENTITIES.supporttickets.url + '?limit=1' }),
      ajax({ url: API_BASE + ENTITIES.interactions.url + '?limit=1' })
    ).done(function(clientsRes, leadsRes, oppsRes, ticketsRes, interactionsRes){
      try {
        $('#kpi-clients').text(clientsRes[0].count ?? (clientsRes[0].length || 0));
        $('#kpi-leads').text(leadsRes[0].count ?? (leadsRes[0].length || 0));
        $('#kpi-opps').text(oppsRes[0].count ?? (oppsRes[0].length || 0));
        $('#kpi-tickets').text(ticketsRes[0].count ?? (ticketsRes[0].length || 0));
        $('#kpi-interactions').text(interactionsRes[0].count ?? (interactionsRes[0].length || 0));
      } catch(err) {
        console.warn('[crm][kpi] parsing fallback', err);
      }
    });
  }

  // Generic list fetcher with pagination rendering
  function fetchList(entityKey, pageUrl=null) {
    const ent = ENTITIES[entityKey];
    const $tbody = $(ent.table + ' tbody');
    const pageSize = $('#crm-page-size').val() || 10;
    const search = $('#crm-search').val()?.trim();
    let params = { limit: pageSize };
    if (search) params.search = search;
    const url = pageUrl || (API_BASE + ent.url + '?' + $.param(params));
    ajax({ url: url, type: 'GET' }).done(function(response){
      // DRF default paginated format: {count, next, previous, results}
      const results = response.results ?? response;
      $tbody.empty();
      results.forEach(item => {
        let row = renderRow(entityKey, item);
        $tbody.append(row);
      });
      renderPagination(entityKey, response);
    });
  }

  function renderPagination(entityKey, response) {
    const ent = ENTITIES[entityKey];
    const $pag = $(ent.pag).empty();
    if (!response) return;
    const createLi = (label, url, disabled=false, active=false) => {
      const li = $('<li class="page-item"></li>');
      if(disabled) li.addClass('disabled');
      if(active) li.addClass('active');
      const a = $(`<a class="page-link" href="#">${label}</a>`);
      a.on('click', function(e){
        e.preventDefault();
        if(!url) return;
        fetchList(entityKey, url);
      });
      li.append(a);
      return li;
    };
    // Previous
    $pag.append(createLi('«', response.previous, !response.previous));
    // build page numbers if available (DRF doesn't have page numbers easily; fallback: simple prev/next)
    // Next
    $pag.append(createLi('»', response.next, !response.next));
  }

  // Render row per entity
  function renderRow(entityKey, obj) {
    switch(entityKey) {
      case 'clients':
        return `<tr>
            <td>${obj.id}</td>
            <td>${escapeHtml(obj.name)}</td>
            <td>${escapeHtml(obj.email||'-')}</td>
            <td>${escapeHtml(obj.phone_number||'-')}</td>
            <td>${escapeHtml(obj.company_name||'-')}</td>
            <td>
              <button class="btn btn-sm btn-warning crm-edit" data-entity="${entityKey}" data-id="${obj.id}">Edit</button>
              <button class="btn btn-sm btn-danger crm-delete" data-entity="${entityKey}" data-id="${obj.id}">Delete</button>
            </td>
          </tr>`;
      case 'leads':
        return `<tr>
            <td>${obj.id}</td>
            <td>${escapeHtml(obj.name)}</td>
            <td>${escapeHtml(obj.email||'-')}</td>
            <td>${escapeHtml(obj.phone_number||'-')}</td>
            <td>${escapeHtml(obj.status)}</td>
            <td>${escapeHtml(obj.source)}</td>
            <td>
              <button class="btn btn-sm btn-warning crm-edit" data-entity="${entityKey}" data-id="${obj.id}">Edit</button>
              <button class="btn btn-sm btn-danger crm-delete" data-entity="${entityKey}" data-id="${obj.id}">Delete</button>
            </td>
          </tr>`;
      case 'opportunities':
        return `<tr>
            <td>${obj.id}</td>
            <td>${escapeHtml(obj.name)}</td>
            <td>${escapeHtml(obj.lead || '-')}</td>
            <td>${escapeHtml(obj.client || '-')}</td>
            <td>${escapeHtml(obj.stage)}</td>
            <td>${obj.amount ?? '-'}</td>
            <td>${obj.expected_close_date ?? '-'}</td>
            <td>
              <button class="btn btn-sm btn-warning crm-edit" data-entity="${entityKey}" data-id="${obj.id}">Edit</button>
              <button class="btn btn-sm btn-danger crm-delete" data-entity="${entityKey}" data-id="${obj.id}">Delete</button>
            </td>
          </tr>`;
      case 'supporttickets':
        return `<tr>
            <td>${obj.id}</td>
            <td>${escapeHtml(obj.client || '-')}</td>
            <td>${escapeHtml(obj.subject)}</td>
            <td>${escapeHtml(obj.status)}</td>
            <td>${escapeHtml(obj.priority)}</td>
            <td>
              <button class="btn btn-sm btn-warning crm-edit" data-entity="${entityKey}" data-id="${obj.id}">Edit</button>
              <button class="btn btn-sm btn-danger crm-delete" data-entity="${entityKey}" data-id="${obj.id}">Delete</button>
            </td>
          </tr>`;
      case 'interactions':
        return `<tr>
            <td>${obj.id}</td>
            <td>${escapeHtml(obj.client || '-')}</td>
            <td>${escapeHtml(obj.interaction_type)}</td>
            <td>${escapeHtml(obj.subject || '-')}</td>
            <td>${escapeHtml(obj.interaction_date)}</td>
            <td>
              <button class="btn btn-sm btn-warning crm-edit" data-entity="${entityKey}" data-id="${obj.id}">Edit</button>
              <button class="btn btn-sm btn-danger crm-delete" data-entity="${entityKey}" data-id="${obj.id}">Delete</button>
            </td>
          </tr>`;
      default:
        return `<tr><td colspan="6">Unknown entity</td></tr>`;
    }
  }

  // escape helper
  function escapeHtml(str) {
    return String(str === null || str === undefined ? '' : str)
      .replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;')
      .replaceAll('"','&quot;').replaceAll("'", '&#039;');
  }

  // Render modal form body per entity (simple fields)
  function modalFormHtml(entityKey, data={}) {
    if(entityKey === 'clients') {
      return `
        <div class="mb-3"><label>Name</label><input id="f-name" class="form-control" required value="${escapeHtml(data.name||'')}"></div>
        <div class="mb-3"><label>Email</label><input id="f-email" class="form-control" value="${escapeHtml(data.email||'')}"></div>
        <div class="mb-3"><label>Phone</label><input id="f-phone" class="form-control" value="${escapeHtml(data.phone_number||'')}"></div>
        <div class="mb-3"><label>Company</label><input id="f-company" class="form-control" value="${escapeHtml(data.company_name||'')}"></div>
      `;
    }
    if(entityKey === 'leads') {
      return `
        <div class="mb-3"><label>Name</label><input id="f-name" class="form-control" required value="${escapeHtml(data.name||'')}"></div>
        <div class="mb-3"><label>Email</label><input id="f-email" class="form-control" value="${escapeHtml(data.email||'')}"></div>
        <div class="mb-3"><label>Phone</label><input id="f-phone" class="form-control" value="${escapeHtml(data.phone_number||'')}"></div>
        <div class="mb-3"><label>Status</label>
          <select id="f-status" class="form-select">
            <option value="new">New</option><option value="contacted">Contacted</option>
            <option value="qualified">Qualified</option><option value="unqualified">Unqualified</option>
            <option value="converted">Converted</option>
          </select></div>
        <div class="mb-3"><label>Source</label>
          <select id="f-source" class="form-select">
            <option value="website">Website</option><option value="referral">Referral</option>
            <option value="email_campaign">Email Campaign</option><option value="phone">Phone</option>
            <option value="social_media">Social Media</option><option value="other">Other</option>
          </select></div>
        <div class="mb-3"><label>Notes</label><textarea id="f-notes" class="form-control">${escapeHtml(data.notes||'')}</textarea></div>
      `;
    }
    if(entityKey === 'opportunities') {
      return `
        <div class="mb-3"><label>Name</label><input id="f-name" class="form-control" required value="${escapeHtml(data.name||'')}"></div>
        <div class="mb-3"><label>Lead ID (optional)</label><input id="f-lead" type="number" class="form-control" value="${escapeHtml(data.lead||'')}"></div>
        <div class="mb-3"><label>Client ID</label><input id="f-client" type="number" class="form-control" required value="${escapeHtml(data.client||'')}"></div>
        <div class="mb-3"><label>Stage</label>
          <select id="f-stage" class="form-select">
            <option value="prospecting">Prospecting</option><option value="qualification">Qualification</option>
            <option value="proposal">Proposal</option><option value="negotiation">Negotiation</option>
            <option value="closed_won">Closed Won</option><option value="closed_lost">Closed Lost</option>
          </select></div>
        <div class="mb-3"><label>Expected Close</label><input id="f-expected_close_date" type="date" class="form-control" value="${data.expected_close_date||''}"></div>
        <div class="mb-3"><label>Amount</label><input id="f-amount" type="number" step="0.01" class="form-control" value="${data.amount||''}"></div>
        <div class="mb-3"><label>Probability</label><input id="f-probability" type="number" step="0.01" class="form-control" value="${data.probability||0}"></div>
      `;
    }
    if(entityKey === 'supporttickets') {
      return `
        <div class="mb-3"><label>Client ID</label><input id="f-client" type="number" class="form-control" required value="${escapeHtml(data.client||'')}"></div>
        <div class="mb-3"><label>Subject</label><input id="f-subject" class="form-control" required value="${escapeHtml(data.subject||'')}"></div>
        <div class="mb-3"><label>Description</label><textarea id="f-description" class="form-control">${escapeHtml(data.description||'')}</textarea></div>
        <div class="mb-3"><label>Status</label><select id="f-status" class="form-select">
            <option value="open">Open</option><option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option><option value="closed">Closed</option></select></div>
        <div class="mb-3"><label>Priority</label><select id="f-priority" class="form-select">
            <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></div>
      `;
    }
    if(entityKey === 'interactions') {
      return `
        <div class="mb-3"><label>Client ID</label><input id="f-client" type="number" class="form-control" required value="${escapeHtml(data.client||'')}"></div>
        <div class="mb-3"><label>Type</label><select id="f-type" class="form-select">
            <option value="call">Call</option><option value="email">Email</option><option value="meeting">Meeting</option>
            <option value="chat">Chat</option><option value="note">Note</option></select></div>
        <div class="mb-3"><label>Subject</label><input id="f-subject" class="form-control" value="${escapeHtml(data.subject||'')}"></div>
        <div class="mb-3"><label>Description</label><textarea id="f-description" class="form-control">${escapeHtml(data.description||'')}</textarea></div>
        <div class="mb-3"><label>Date</label><input id="f-date" type="datetime-local" class="form-control" value="${formatDateTimeLocal(data.interaction_date)||''}"></div>
      `;
    }
    return '<div>Unknown entity</div>';
  }

  function formatDateTimeLocal(dateStr) {
    if(!dateStr) return '';
    const dt = new Date(dateStr);
    const pad = n => n.toString().padStart(2,'0');
    return `${dt.getFullYear()}-${pad(dt.getMonth()+1)}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
  }

  // Open create modal
  $('#btn-add').on('click', function(){
    const active = $('#crmTabs .nav-link.active').attr('id');
    let entityKey = 'clients';
    if(active === 'clients-tab') entityKey = 'clients';
    if(active === 'leads-tab') entityKey = 'leads';
    if(active === 'opps-tab') entityKey = 'opportunities';
    if(active === 'tickets-tab') entityKey = 'supporttickets';
    if(active === 'interactions-tab') entityKey = 'interactions';

    $('#entity-type').val(entityKey);
    $('#entity-id').val('');
    $('#crmModalTitle').text('Create ' + entityKey);
    $('#crm-form-body').html(modalFormHtml(entityKey, {}));
    $('#crmModal').modal('show');
  });

  // Edit handler (delegated)
  $(document).on('click', '.crm-edit', function(){
    const entityKey = $(this).data('entity');
    const id = $(this).data('id');
    $('#entity-type').val(entityKey);
    $('#entity-id').val(id);
    // fetch object
    ajax({ url: API_BASE + ENTITIES[entityKey].url + id + '/', type: 'GET' })
      .done(function(data){ 
        $('#crmModalTitle').text('Edit ' + entityKey);
        $('#crm-form-body').html(modalFormHtml(entityKey, data));
        // if selects need to pre-select:
        setTimeout(()=> {
          // generic pre-select for common selects
          if(data.status) $('#f-status').val(data.status);
          if(data.source) $('#f-source').val(data.source);
          if(data.stage) $('#f-stage').val(data.stage);
          if(data.priority) $('#f-priority').val(data.priority);
          if(data.interaction_type) $('#f-type').val(data.interaction_type);
        }, 50);
        $('#crmModal').modal('show');
      });
  });

  // Delete handler (delegated)
  $(document).on('click', '.crm-delete', function(){
    const entityKey = $(this).data('entity');
    const id = $(this).data('id');
    if(!confirm('Delete this record?')) return;
    ajax({ url: API_BASE + ENTITIES[entityKey].url + id + '/', type: 'DELETE' })
      .done(function(){ toastr.success('Deleted'); reloadActive(); fetchKPIs(); });
  });

  // Submit modal form
  $('#crm-form').on('submit', function(e){
    e.preventDefault();
    const entityKey = $('#entity-type').val();
    const id = $('#entity-id').val();
    const url = API_BASE + ENTITIES[entityKey].url + (id ? id + '/' : '');
    const method = id ? 'PUT' : 'POST';
    // Collect payload based on entity
    let payload = {};
    if(entityKey === 'clients'){
      payload = { name: $('#f-name').val(), email: $('#f-email').val(), phone_number: $('#f-phone').val(), company_name: $('#f-company').val() };
    } else if(entityKey === 'leads'){
      payload = { name: $('#f-name').val(), email: $('#f-email').val(), phone_number: $('#f-phone').val(), status: $('#f-status').val(), source: $('#f-source').val(), notes: $('#f-notes').val() };
    } else if(entityKey === 'opportunities'){
      payload = { name: $('#f-name').val(), lead: $('#f-lead').val() || null, client: $('#f-client').val(), stage: $('#f-stage').val(), expected_close_date: $('#f-expected_close_date').val(), amount: $('#f-amount').val(), probability: $('#f-probability').val() };
    } else if(entityKey === 'supporttickets'){
      payload = { client: $('#f-client').val(), subject: $('#f-subject').val(), description: $('#f-description').val(), status: $('#f-status').val(), priority: $('#f-priority').val() };
    } else if(entityKey === 'interactions'){
      payload = { client: $('#f-client').val(), interaction_type: $('#f-type').val(), subject: $('#f-subject').val(), description: $('#f-description').val(), interaction_date: $('#f-date').val() };
    }

    ajax({ url: url, type: method, data: payload })
      .done(function(res){
        toastr.success('Saved successfully');
        $('#crmModal').modal('hide');
        $('#crm-form')[0].reset();
        $('#entity-id').val('');
        reloadActive();
        fetchKPIs();
      });
  });

  // Search and page size change hooks
  $('#crm-search').on('keypress', function(e){
    if(e.which === 13) { reloadActive(); }
  });
  $('#crm-page-size').on('change', function(){ reloadActive(); });

  // When tab changes, reload corresponding list
  $('#crmTabs button[data-bs-toggle="tab"]').on('shown.bs.tab', function (e) {
    reloadActive();
  });

  function reloadActive(){
    const active = $('#crmTabs .nav-link.active').attr('id');
    if(active === 'clients-tab') fetchList('clients');
    if(active === 'leads-tab') fetchList('leads');
    if(active === 'opps-tab') fetchList('opportunities');
    if(active === 'tickets-tab') fetchList('supporttickets');
    if(active === 'interactions-tab') fetchList('interactions');
  }

  // initial load
  fetchKPIs();
  fetchList('clients'); // initial tab
  // also poll KPIs occasionally (optional)
  setInterval(fetchKPIs, 60000);

})();
