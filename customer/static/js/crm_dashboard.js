document.addEventListener('alpine:init', () => {
    Alpine.data('crmDashboard', () => ({
        activeTab: 'clients',
        loading: false,
        items: [],
        totalCount: 0,
        kpis: { clients: 0, leads: 0, opportunities: 0, supporttickets: 0, interactions: 0 },
        search: '',
        pageSize: 10,
        nextUrl: null,
        prevUrl: null,
        modalInstance: null,
        formData: {},
        entityId: null,

        // Configuration Map
        entities: {
            clients: { 
                url: 'clients/', label: 'Client', 
                headers: ['ID', 'Name', 'Email', 'Company'], 
                cols: ['id', 'name', 'email', 'company_name'],
                formFields: [
                    { name: 'name', label: 'Name', type: 'text', fullWidth: true },
                    { name: 'email', label: 'Email', type: 'text' },
                    { name: 'phone_number', label: 'Phone', type: 'text' },
                    { name: 'company_name', label: 'Company', type: 'text', fullWidth: true }
                ]
            },
            leads: { 
                url: 'leads/', label: 'Lead', 
                headers: ['ID', 'Name', 'Status', 'Source'], 
                cols: ['id', 'name', 'status', 'source'],
                formFields: [
                    { name: 'name', label: 'Name', type: 'text', fullWidth: true },
                    { name: 'status', label: 'Status', type: 'select', options: [
                        {val: 'new', label: 'New'}, {val: 'contacted', label: 'Contacted'}, {val: 'qualified', label: 'Qualified'}
                    ]},
                    { name: 'source', label: 'Source', type: 'select', options: [
                        {val: 'website', label: 'Website'}, {val: 'referral', label: 'Referral'}
                    ]}
                ]
            },
            opportunities: { 
                url: 'opportunities/', label: 'Opportunity', 
                headers: ['ID', 'Name', 'Stage', 'Amount'], 
                cols: ['id', 'name', 'stage', 'amount'],
                formFields: [
                    { name: 'name', label: 'Name', type: 'text', fullWidth: true },
                    { name: 'amount', label: 'Amount', type: 'number' },
                    { name: 'stage', label: 'Stage', type: 'select', options: [
                        {val: 'prospecting', label: 'Prospecting'}, {val: 'proposal', label: 'Proposal'}, {val: 'closed_won', label: 'Closed Won'}
                    ]}
                ]
            },
            supporttickets: { 
                url: 'support-tickets/', label: 'Ticket', 
                headers: ['ID', 'Subject', 'Status', 'Priority'], 
                cols: ['id', 'subject', 'status', 'priority'],
                formFields: [
                    { name: 'subject', label: 'Subject', type: 'text', fullWidth: true },
                    { name: 'status', label: 'Status', type: 'select', options: [
                        {val: 'open', label: 'Open'}, {val: 'closed', label: 'Closed'}
                    ]}
                ]
            },
            interactions: { 
                url: 'interactions/', label: 'Interaction', 
                headers: ['ID', 'Type', 'Subject', 'Date'], 
                cols: ['id', 'interaction_type', 'subject', 'interaction_date'],
                formFields: [
                    { name: 'subject', label: 'Subject', type: 'text', fullWidth: true },
                    { name: 'interaction_type', label: 'Type', type: 'select', options: [
                        {val: 'call', label: 'Call'}, {val: 'email', label: 'Email'}
                    ]}
                ]
            }
        },

        async init() {
            this.modalInstance = new bootstrap.Modal(this.$refs.modal);
            await this.fetchData();
            this.syncKPIs();
        },

        async fetchData(url = null) {
            this.loading = true;
            const endpoint = this.entities[this.activeTab].url;
            const targetUrl = url || `/customers/v1/${endpoint}?limit=${this.pageSize}&search=${this.search}`;
            
            try {
                const res = await fetch(targetUrl, { headers: this.getHeaders() });
                const data = await res.json();
                this.items = data.results || [];
                this.totalCount = data.count || this.items.length;
                this.nextUrl = data.next;
                this.prevUrl = data.previous;
            } finally {
                this.loading = false;
            }
        },

        async syncKPIs() {
            const keys = Object.keys(this.entities);
            const requests = keys.map(k => fetch(`/customers/v1/${this.entities[k].url}?limit=1`, { headers: this.getHeaders() }));
            const responses = await Promise.all(requests);
            const results = await Promise.all(responses.map(r => r.json()));
            keys.forEach((key, i) => this.kpis[key] = results[i].count || 0);
        },

        async openModal(id = null) {
            this.entityId = id;
            if (id) {
                const res = await fetch(`/customers/v1/${this.entities[this.activeTab].url}${id}/`, { headers: this.getHeaders() });
                this.formData = await res.json();
            } else {
                this.formData = {};
            }
            this.modalInstance.show();
        },

        async save() {
            const method = this.entityId ? 'PUT' : 'POST';
            const url = `/customers/v1/${this.entities[this.activeTab].url}${this.entityId ? this.entityId + '/' : ''}`;
            
            const res = await fetch(url, {
                method: method,
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.CSRF_TOKEN,
                },
                body: JSON.stringify(this.formData)
            });

            if (res.ok) {
                this.modalInstance.hide();
                this.fetchData();
                this.syncKPIs();
            }
        },

        async deleteItem(id) {
            if (!confirm('Are you sure?')) return;
            await fetch(`/customerCRM/api/${this.entities[this.activeTab].url}${id}/`, { 
                method: 'DELETE', 
                headers: this.getHeaders() 
            });
            this.fetchData();
            this.syncKPIs();
        },

        renderCell(item, col) {
            return item[col] || '-';
        },

        switchTab(tab) {
            this.activeTab = tab;
            this.search = '';
            this.fetchData();
        },

        getHeaders() {
            return { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value };
        }
    }));
});