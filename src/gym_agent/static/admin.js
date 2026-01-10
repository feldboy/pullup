/**
 * GymAI Admin Dashboard Logic
 */

// State
let currentTab = 'config';
let customers = [];
let debounceTimer;

// Init
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    loadCustomers();
});

// Tabs
function switchTab(tabName) {
    currentTab = tabName;

    // UI Update
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');

    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.getElementById(`tab-${tabName}`).classList.add('active');

    // Refresh data
    if (tabName === 'config') loadConfig();
    if (tabName === 'customers') loadCustomers();
}

// Config
async function loadConfig() {
    try {
        const res = await fetch('/api/admin/config?key=system_prompt');
        const data = await res.json();
        document.getElementById('systemPromptEditor').value = data.value || '';
    } catch (e) {
        console.error("Failed to load config", e);
    }
}

async function saveConfig() {
    const value = document.getElementById('systemPromptEditor').value;
    const btn = document.querySelector('button[onclick="saveConfig()"]');
    const originalText = btn.innerText;

    btn.innerText = "שומר...";
    btn.disabled = true;

    try {
        await fetch('/api/admin/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                key: 'system_prompt',
                value: value
            })
        });

        showToast("ההגדרות נשמרו בהצלחה!");
    } catch (e) {
        alert("שגיאה בשמירה: " + e.message);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// Customers
async function loadCustomers(search = "") {
    let url = '/api/v1/customers';
    if (search) url += `?search=${encodeURIComponent(search)}`;

    try {
        const res = await fetch(url);
        customers = await res.json();
        renderTable();
    } catch (e) {
        console.error("Failed to load customers", e);
    }
}

function renderTable() {
    const tbody = document.getElementById('customersTable');
    tbody.innerHTML = '';

    customers.forEach(c => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <div style="font-weight: 500;">${c.name}</div>
                <div style="font-size: 0.8rem; color: var(--text-secondary);">${c.crm_id}</div>
            </td>
            <td>${c.phone}</td>
            <td><span class="status-badge status-${c.status}">${c.status}</span></td>
            <td>
                <div class="health-bar-container">
                    <div class="health-bar" style="width: ${c.health_score}%; background: ${getHealthColor(c.health_score)}"></div>
                </div>
                <span style="font-size: 0.8rem;">${c.health_score}/100</span>
            </td>
            <td>${c.membership_type}</td>
            <td>
                <button class="btn btn-secondary" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;" onclick="editCustomer('${c.id}')">ערוך</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function getHealthColor(score) {
    if (score >= 80) return 'var(--success-color)';
    if (score >= 50) return 'var(--warning-color)';
    return 'var(--danger-color)';
}

function debounceSearch() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        const val = document.getElementById('searchInput').value;
        loadCustomers(val);
    }, 300);
}

// Edit Modal
let editingCustomerId = null;

async function editCustomer(id) {
    editingCustomerId = id;
    const customer = customers.find(c => c.id === id);
    if (!customer) return;

    // Name split for form
    const names = customer.name.split(' ');
    const first = names[0];
    const last = names.slice(1).join(' ');

    document.getElementById('editId').value = id;
    document.getElementById('editFirstName').value = first;
    document.getElementById('editLastName').value = last;
    document.getElementById('editHealthScore').value = customer.health_score;
    document.getElementById('editStatus').value = customer.status;

    document.getElementById('editModal').classList.add('active');
}

function closeModal() {
    document.getElementById('editModal').classList.remove('active');
    editingCustomerId = null;
}

async function submitCustomerEdit(e) {
    e.preventDefault();
    if (!editingCustomerId) return;

    const data = {
        first_name: document.getElementById('editFirstName').value,
        last_name: document.getElementById('editLastName').value,
        health_score: parseInt(document.getElementById('editHealthScore').value),
        status: document.getElementById('editStatus').value,
        manual_notes: document.getElementById('editNotes').value
    };

    try {
        const res = await fetch(`/api/admin/customers/${editingCustomerId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!res.ok) throw new Error("Update failed");

        closeModal();
        loadCustomers(); // Reload list
        showToast("הלקוח עודכן בהצלחה!");

    } catch (e) {
        alert("שגיאה בעדכון: " + e.message);
    }
}

function showToast(msg) {
    // Simple alert for MVP, or implement toast if time
    alert(msg);
}
