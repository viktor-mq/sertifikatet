

/**
 * Shared Admin Enhancements
 */
(function(window) {
  const AdminEnhancements = {};

  /**
   * Fetch JSON data from the API with query parameters.
   * @param {string} resource
   * @param {object} params
   */
  AdminEnhancements.fetchData = async function(resource, params = {}) {
    const query = new URLSearchParams(params).toString();
    const url = `/admin/api/${resource}` + (query ? `?${query}` : '');
    const response = await fetch(url, {
      headers: { 'Accept': 'application/json' }
    });
    if (!response.ok) {
      throw new Error(`Failed to fetch ${resource}: ${response.statusText}`);
    }
    return response.json();
  };

  /**
   * Display a transient toast notification.
   * @param {string} message
   * @param {string} [type="info"] - "info", "success", or "error"
   */
  AdminEnhancements.showToast = function(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerText = message;
    container.appendChild(toast);
    setTimeout(() => container.removeChild(toast), 3000);
  };

  /**
   * Initialize server‐side filtering behavior.
   * @param {object} options
   * @param {string} options.resource
   * @param {string} [options.formSelector="#filter-form"]
   * @param {string} [options.tableSelector="#data-table"]
   */
  AdminEnhancements.initializeFiltering = function({ resource, formSelector = '#filter-form', tableSelector = '#data-table' }) {
    const form = document.querySelector(formSelector);
    if (!form) return;
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const params = Object.fromEntries(new FormData(form));
      try {
        const data = await AdminEnhancements.fetchData(resource, params);
        AdminEnhancements.renderTable(data, tableSelector);
      } catch (err) {
        AdminEnhancements.showToast(err.message, 'error');
      }
    });
  };

  /**
   * Initialize pagination controls.
   * @param {object} options
   * @param {string} options.resource
   * @param {string} [options.tableSelector="#data-table"]
   * @param {string} [options.paginationSelector="#pagination"]
   */
  AdminEnhancements.initializePagination = function({ resource, tableSelector = '#data-table', paginationSelector = '#pagination' }) {
    const pagination = document.querySelector(paginationSelector);
    if (!pagination) return;
    pagination.addEventListener('click', async (e) => {
      if (e.target.matches('.page-link')) {
        e.preventDefault();
        const page = e.target.dataset.page;
        try {
          const data = await AdminEnhancements.fetchData(resource, { page });
          AdminEnhancements.renderTable(data, tableSelector);
        } catch (err) {
          AdminEnhancements.showToast(err.message, 'error');
        }
      }
    });
  };

  /**
   * Initialize sortable column headers.
   * @param {object} options
   * @param {string} options.resource
   * @param {string} [options.tableSelector="#data-table"]
   */
  AdminEnhancements.initializeSorting = function({ resource, tableSelector = '#data-table' }) {
    const table = document.querySelector(tableSelector);
    if (!table) return;
    table.addEventListener('click', async (e) => {
      if (e.target.matches('th.sortable')) {
        const sortBy = e.target.dataset.field;
        const currentOrder = e.target.dataset.order || 'asc';
        const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
        e.target.dataset.order = newOrder;
        try {
          const data = await AdminEnhancements.fetchData(resource, { sort_by: sortBy, sort_order: newOrder });
          AdminEnhancements.renderTable(data, tableSelector);
        } catch (err) {
          AdminEnhancements.showToast(err.message, 'error');
        }
      }
    });
  };

  /**
   * Initialize create/edit modals.
   * @param {object} options
   * @param {string} options.resource
   * @param {string} [options.modalSelector="#edit-modal"]
   * @param {string} [options.formSelector="#edit-form"]
   */
  AdminEnhancements.initializeModals = function({ resource, modalSelector = '#edit-modal', formSelector = '#edit-form' }) {
    const modal = document.querySelector(modalSelector);
    if (!modal) return;
    const form = modal.querySelector(formSelector);
    const saveBtn = modal.querySelector('.save-btn');
    saveBtn.addEventListener('click', async () => {
      const payload = Object.fromEntries(new FormData(form));
      try {
        const response = await fetch(`/admin/api/${resource}/update/${payload.id}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error(`Save failed: ${response.statusText}`);
        AdminEnhancements.showToast('Saved successfully', 'success');
        modal.classList.remove('is-active');
        const data = await AdminEnhancements.fetchData(resource, {});
        AdminEnhancements.renderTable(data, '#data-table');
      } catch (err) {
        AdminEnhancements.showToast(err.message, 'error');
      }
    });
    modal.querySelector('.close-btn').addEventListener('click', () => modal.classList.remove('is-active'));
  };

  /**
   * Render table rows from JSON data.
   * @param {object} data
   * @param {string} tableSelector
   */
  AdminEnhancements.renderTable = function(data, tableSelector) {
    const tbody = document.querySelector(`${tableSelector} tbody`);
    if (!tbody) return;
    tbody.innerHTML = '';
    data.items.forEach(item => {
      const row = document.createElement('tr');
      Object.values(item).forEach(val => {
        const td = document.createElement('td');
        td.innerText = val;
        row.appendChild(td);
      });
      tbody.appendChild(row);
    });
  };

  // Expose globally
  window.AdminEnhancements = AdminEnhancements;
})(window);