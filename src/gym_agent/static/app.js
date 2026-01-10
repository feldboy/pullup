console.log("Ralph CRM Loaded");

const API_BASE = '/api/v1';

const app = {
    state: {
        currentView: 'dashboard',
        customers: [],
        currentCustomer: null,
        stats: null
    },

    init: function () {
        console.log("App initializing...");
        this.bindEvents();
        this.loadView('dashboard');
    },

    bindEvents: function () {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const viewId = item.dataset.view;
                this.navigate(viewId);
            });
        });

        // Search
        const searchInput = document.getElementById('global-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.handleSearch(e.target.value);
            }, 300));
        }

        // Filter Select
        const filterSelect = document.querySelector('.table-actions select');
        if (filterSelect) {
            filterSelect.addEventListener('change', (e) => {
                this.loadCustomers({ status: e.target.value !== 'all' ? e.target.value : null });
            });
        }
    },

    navigate: function (viewId) {
        console.log("Navigating to", viewId);

        // Update UI
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        document.getElementById(`view-${viewId}`).classList.add('active');

        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        // Find by data-view attribute (handle nested if needed, but here straightforward)
        const navItem = document.querySelector(`.nav-item[data-view="${viewId}"]`);
        if (navItem) navItem.classList.add('active');

        this.state.currentView = viewId;
        this.loadView(viewId);
    },

    loadView: async function (viewId) {
        switch (viewId) {
            case 'dashboard':
                await this.loadStats();
                await this.loadRecentActivity();
                break;
            case 'customers':
                await this.loadCustomers();
                break;
            case 'analytics':
                await this.loadAnalytics();
                break;
            case 'settings':
                await this.loadSettings();
                break;
        }
    },

    // API Calls
    loadStats: async function () {
        try {
            const response = await fetch(`${API_BASE}/dashboard/stats`);
            const stats = await response.json();
            this.state.stats = stats;
            this.renderStats(stats);
        } catch (error) {
            console.error("Failed to load stats:", error);
        }
    },

    loadCustomers: async function (filters = {}) {
        const tbody = document.getElementById('customers-table-body');
        if (!tbody) return;

        tbody.innerHTML = '<tr><td colspan="6" class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></td></tr>';

        try {
            let url = `${API_BASE}/customers`;
            const params = new URLSearchParams();
            if (filters.search) params.append('search', filters.search);
            if (filters.status) params.append('status', filters.status);
            if (filters.health_below) params.append('health_below', filters.health_below);

            if ([...params].length > 0) url += `?${params.toString()}`;

            const response = await fetch(url);
            const customers = await response.json();
            this.state.customers = customers;
            this.renderCustomers(customers);
        } catch (error) {
            console.error("Failed to load customers:", error);
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--danger)">שגיאה בטעינת נתונים</td></tr>';
        }
    },

    loadRecentActivity: async function () {
        // For dashboard "High Risk" list
        try {
            // Re-use customer search API for risk
            const response = await fetch(`${API_BASE}/customers?status=at_risk`);
            const riskCustomers = await response.json();
            this.renderRiskList(riskCustomers);

            // Recent chats placeholder (API not fully ready for "all recent chats", we'll verify customer chat later)
            // But we can list active customers as proxy for recent activity
            const activeResp = await fetch(`${API_BASE}/customers?status=active`);
            const activeCustomers = await activeResp.json();
            this.renderRecentChats(activeCustomers.slice(0, 5));
        } catch (e) {
            console.error(e);
        }
    },

    loadCustomerDetail: async function (customerId) {
        this.navigate('customer-detail');
        const container = document.querySelector('#view-customer-detail .profile-card');
        container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

        try {
            const [customer, conversations] = await Promise.all([
                fetch(`${API_BASE}/customers/${customerId}`).then(r => r.json()),
                fetch(`${API_BASE}/conversations/${customerId}`).then(r => r.json())
            ]);

            this.state.currentCustomer = customer;
            this.renderCustomerProfile(customer);
            this.renderChatHistory(conversations);
        } catch (e) {
            console.error("Failed to load detail:", e);
        }
    },

    loadAnalytics: async function () {
        const statusChart = document.getElementById('status-chart');
        const membershipChart = document.getElementById('membership-chart');

        try {
            const response = await fetch(`${API_BASE}/dashboard/stats`);
            const data = await response.json();

            this.renderChart(statusChart, data.distributions?.status || {});
            this.renderChart(membershipChart, data.distributions?.membership || {});
        } catch (e) {
            console.error(e);
            statusChart.innerHTML = 'Error loading data';
        }
    },

    loadSettings: async function () {
        // Mock loading settings
        document.getElementById('env-badge').innerText = 'DEV'; // In real app, fetch from API
    },

    renderChart: function (container, data) {
        if (!container) return;

        // Convert to array and sort
        const items = Object.entries(data).sort((a, b) => b[1] - a[1]);
        const max = Math.max(...Object.values(data), 1);

        container.innerHTML = items.map(([label, value]) => `
            <div style="margin-bottom:10px">
                <div style="display:flex;justify-content:space-between;font-size:0.9rem;margin-bottom:4px">
                    <span>${this.translateStatus(label)}</span>
                    <span>${value}</span>
                </div>
                <div style="width:100%;height:8px;background:rgba(255,255,255,0.1);border-radius:4px;overflow:hidden">
                    <div style="width:${(value / max) * 100}%;height:100%;background:var(--accent-color)"></div>
                </div>
            </div>
        `).join('');
    },

    // Rendering
    renderStats: function (stats) {
        if (!stats) return;
        this.updateStat('total_customers', stats.total_customers);
        this.updateStat('active_customers', stats.active_customers);
        this.updateStat('at_risk_customers', stats.at_risk_customers);
        this.updateStat('visits_today', stats.visits_today || 0);
    },

    updateStat: function (key, value) {
        const el = document.querySelector(`[data-stat="${key}"]`);
        if (el) el.innerText = value;
    },

    renderCustomers: function (customers) {
        const tbody = document.getElementById('customers-table-body');
        if (!tbody) return;

        if (customers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px">לא נמצאו לקוחות</td></tr>';
            return;
        }

        tbody.innerHTML = customers.map(c => `
            <tr onclick="app.loadCustomerDetail('${c.id}')" style="cursor:pointer">
                <td>
                    <div style="font-weight:500">${c.name}</div>
                    <div style="font-size:0.8rem;color:var(--text-secondary)">${c.crm_id}</div>
                </td>
                <td><span class="badge ${c.status}">${this.translateStatus(c.status)}</span></td>
                <td>
                    <div class="health-indicator">
                        <div class="bar" style="width:${c.health_score}%;background:${this.getHealthColor(c.health_score)}"></div>
                        <span>${c.health_score}</span>
                    </div>
                </td>
                <td>${c.days_since_visit} ימים</td>
                <td>${c.membership_type === 'unlimited' ? 'ללא הגבלה' : c.membership_type}</td>
                <td>
                    <button class="icon-btn sm"><i class="fas fa-comment-dots"></i></button>
                    <button class="icon-btn sm"><i class="fas fa-ellipsis-v"></i></button>
                </td>
            </tr>
        `).join('');
    },

    renderRiskList: function (customers) {
        const list = document.getElementById('risk-list');
        if (!list) return;

        if (customers.length === 0) {
            list.innerHTML = '<div style="padding:10px;text-align:center;color:var(--text-secondary)">אין לקוחות בסיכון</div>';
            return;
        }

        list.innerHTML = customers.map(c => `
            <div class="list-item" onclick="app.loadCustomerDetail('${c.id}')" style="cursor:pointer;padding:10px;border-bottom:1px solid var(--glass-border);display:flex;justify-content:space-between;align-items:center">
                <div>
                    <div style="font-weight:500">${c.name}</div>
                    <div style="font-size:0.8rem;color:var(--danger)">בריאות: ${c.health_score}</div>
                </div>
                <i class="fas fa-chevron-left" style="color:var(--text-secondary)"></i>
            </div>
        `).join('');
    },

    renderRecentChats: function (customers) {
        const list = document.getElementById('recent-chats');
        if (!list) return;

        list.innerHTML = customers.map(c => `
             <div class="list-item" onclick="app.loadCustomerDetail('${c.id}')" style="cursor:pointer;padding:10px;border-bottom:1px solid var(--glass-border);display:flex;align-items:center;gap:10px">
                 <div class="avatar sm" style="width:32px;height:32px;font-size:0.8rem">${c.name[0]}</div>
                 <div>
                     <div style="font-weight:500">${c.name}</div>
                     <div style="font-size:0.8rem;color:var(--text-secondary)">לחץ לצפייה בשיחה</div>
                 </div>
             </div>
         `).join('');
    },

    renderCustomerProfile: function (c) {
        const container = document.querySelector('#view-customer-detail .profile-card');
        container.innerHTML = `
            <div style="display:flex;align-items:center;gap:20px;margin-bottom:20px">
                <div class="avatar lg" style="width:80px;height:80px;font-size:2rem">${c.name[0]}</div>
                <div>
                    <h2 style="font-size:2rem">${c.name}</h2>
                    <div class="badges">
                        <span class="badge ${c.status}">${this.translateStatus(c.status)}</span>
                        <span class="badge membership">${c.membership.type}</span>
                    </div>
                </div>
            </div>
            
            <div class="info-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
                <div class="info-item">
                    <label>טלפון</label>
                    <div>${c.phone}</div>
                </div>
                <div class="info-item">
                    <label>אימייל</label>
                    <div>${c.email || '-'}</div>
                </div>
                <div class="info-item">
                    <label>תוקף מנוי</label>
                    <div>${c.membership.end_date || '-'} (${c.membership.days_remaining} ימים)</div>
                </div>
                <div class="info-item">
                    <label>ביקורים</label>
                    <div>${c.activity.total_visits} (אחרון: ${c.activity.days_since_visit} ימים)</div>
                </div>
            </div>
            
            <div class="health-card" style="margin-top:20px;padding:15px;background:rgba(0,0,0,0.2);border-radius:12px">
                <h3>ציון בריאות: ${c.health_score.total}</h3>
                <div class="bar" style="height:6px;width:100%;background:#333;margin-top:10px;border-radius:3px">
                    <div style="height:100%;width:${c.health_score.total}%;background:${this.getHealthColor(c.health_score.total)};border-radius:3px"></div>
                </div>
            </div>
        `;
    },

    renderChatHistory: function (conversations) {
        const container = document.querySelector('#view-customer-detail .chat-card');
        if (!conversations || conversations.length === 0) {
            container.innerHTML = `
                <div style="padding:20px;text-align:center">אין היסטורית שיחות</div>
                <div class="chat-input" style="padding:15px;border-top:1px solid var(--glass-border);display:flex;gap:10px;margin-top:auto">
                    <input type="text" id="chat-input-text" placeholder="התחל שיחה..." style="flex:1;background:rgba(0,0,0,0.2);border:none;padding:10px;border-radius:8px;color:white">
                    <button class="btn-primary" onclick="app.handleSendReply()" style="background:var(--accent-color);border:none;width:40px;border-radius:8px;cursor:pointer"><i class="fas fa-paper-plane"></i></button>
                </div>
            `;
            return;
        }

        // Take the latest conversation
        const activeConv = conversations[0];

        container.innerHTML = `
            <div class="chat-header" style="padding:15px;border-bottom:1px solid var(--glass-border)">
                <h3>שיחה פעילה</h3>
                <span class="status-dot ${activeConv.status}"></span>
            </div>
            <div class="messages" id="chat-messages" style="height:400px;overflow-y:auto;padding:15px;display:flex;flex-direction:column;gap:15px">
                ${activeConv.messages.map(m => `
                    <div class="message ${m.direction}" style="
                        align-self: ${m.direction === 'outbound' ? 'flex-start' : 'flex-end'};
                        background: ${m.direction === 'outbound' ? 'rgba(255,255,255,0.1)' : 'var(--primary-color)'};
                        padding: 10px 14px;
                        border-radius: 12px;
                        max-width: 70%;
                        ${m.direction === 'outbound' ? 'border-top-right-radius:2px' : 'border-top-left-radius:2px'};
                    ">
                        <div class="msg-content">${m.content}</div>
                        <div class="msg-meta" style="font-size:0.7rem;opacity:0.7;margin-top:4px;text-align:left">
                            ${new Date(m.created_at).toLocaleTimeString()}
                            ${m.intent ? `• ${m.intent}` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
            <div class="chat-input" style="padding:15px;border-top:1px solid var(--glass-border);display:flex;gap:10px">
                <input type="text" id="chat-input-text" placeholder="הקלד הודעה..." style="flex:1;background:rgba(0,0,0,0.2);border:none;padding:10px;border-radius:8px;color:white" onkeypress="if(event.key==='Enter') app.handleSendReply()">
                <button class="btn-primary" onclick="app.handleSendReply()" style="background:var(--accent-color);border:none;width:40px;border-radius:8px;cursor:pointer"><i class="fas fa-paper-plane"></i></button>
            </div>
        `;

        // Scroll to bottom
        const messagesDiv = document.getElementById('chat-messages');
        if (messagesDiv) messagesDiv.scrollTop = messagesDiv.scrollHeight;
    },

    handleSendReply: async function () {
        if (!this.state.currentCustomer) return;

        const input = document.getElementById('chat-input-text');
        const message = input.value.trim();

        if (!message) return;

        // Optimistic UI update (optional, but let's wait for success)
        input.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/conversations/${this.state.currentCustomer.id}/reply`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, channel: 'telegram' })
            });

            if (!res.ok) throw new Error('Failed to send');

            // Append message
            const messagesDiv = document.getElementById('chat-messages');
            if (messagesDiv) {
                const now = new Date();
                messagesDiv.innerHTML += `
                    <div class="message outbound" style="
                        align-self: flex-start;
                        background: rgba(255,255,255,0.1);
                        padding: 10px 14px;
                        border-radius: 12px;
                        max-width: 70%;
                        border-top-right-radius:2px;
                    ">
                        <div class="msg-content">${message}</div>
                        <div class="msg-meta" style="font-size:0.7rem;opacity:0.7;margin-top:4px;text-align:left">
                            ${now.toLocaleTimeString()} • human
                        </div>
                    </div>
                `;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            input.value = '';
        } catch (e) {
            console.error(e);
            alert('שגיאה בשליחת הודעה: ' + e.message);
        } finally {
            input.disabled = false;
            input.focus();
        }
    },

    // Helpers
    handleSearch: function (query) {
        this.loadCustomers({ search: query });
    },

    debounce: function (func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    translateStatus: function (status) {
        const map = {
            'active': 'פעיל',
            'at_risk': 'בסיכון',
            'inactive': 'לא פעיל',
            'cancelled': 'מבוטל'
        };
        return map[status] || status;
    },

    getHealthColor: function (score) {
        if (score >= 80) return 'var(--success)';
        if (score >= 50) return 'var(--warning)';
        return 'var(--danger)';
    }
};

document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
