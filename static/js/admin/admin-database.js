/**
 * Database Section Enhancements
 * Handles multi-table search, filtering, sorting, column toggles, pagination, and export.
 */
(function(window, AdminEnhancements) {
    /**
     * Initialize per-table search inputs.
     */
    function initializeDatabaseSearch() {
      document.querySelectorAll('.search-filter-container').forEach(container => {
        const input = container.querySelector('.search-input');
        if (!input) return;
        let timeout;
        input.addEventListener('input', () => {
          clearTimeout(timeout);
          timeout = setTimeout(() => {
            const term = input.value.trim().toLowerCase();
            const tableName = container.dataset.table;
            const section = document.querySelector(`.table-section[data-table="${tableName}"]`);
            section.querySelectorAll('tbody tr').forEach(row => {
              const text = row.textContent.toLowerCase();
              row.style.display = !term || text.includes(term) ? '' : 'none';
            });
            // After filtering by search, reset pagination to page 1
            document.getElementById(`${tableName}PerPageSelector`).dispatchEvent(new Event('change'));
          }, 300);
        });
      });
    }
  
    // Filter tables dropdown
    function initializeTableSelector() {
      const select = document.getElementById('tableFilter');
      if (!select) return;
      select.addEventListener('change', filterTables);
    }
  
    // Column visibility toggles
    function initializeColumnToggles() {
      document.querySelectorAll('.column-checkbox').forEach(cb => {
        cb.addEventListener('change', () => {
          const table = cb.dataset.table;
          const column = cb.dataset.column;
          const cells = document.querySelectorAll(`.table-section[data-table="${table}"] td[data-column="${column}"], .table-section[data-table="${table}"] th[data-column="${column}"]`);
          cells.forEach(cell => cell.style.display = cb.checked ? '' : 'none');
        });
      });
    }
  
    // Column-specific filters under headers
    function initializeColumnValueFilters() {
      document.querySelectorAll('.column-value-filter').forEach(sel => {
        sel.addEventListener('change', filterTableByColumn);
      });
    }
  
    // Wire up sort clicks on headers
    function initializeSortHeaders() {
      document.querySelectorAll('.sortable').forEach(th => {
        th.addEventListener('click', () => {
          const tableName = th.dataset.table;
          const column = th.dataset.column;
          sortTable(tableName, column);
        });
      });
    }
  
    function initializeExportButtons() {
      document.querySelectorAll('[data-export]').forEach(btn => {
        btn.addEventListener('click', () => {
          const tableName = btn.dataset.table;
          const format = btn.dataset.format;
          exportTableData(tableName, format);
        });
      });
    }
  
    // Initial setup
    document.addEventListener('DOMContentLoaded', () => {
      initializeDatabaseSearch();
      initializeTableSelector();
      initializeColumnToggles();
      initializeColumnValueFilters();
      initializeSortHeaders();
      initializeExportButtons();
      // Initialize client-side pagination per table
      initializeTablePagination();
    });
  
  
    // Functions (reusing AdminEnhancements.showToast for notifications)
  
    function searchAcrossTables() {
      const term = document.getElementById('database-search').value.trim().toLowerCase();
      let totalMatches = 0;
      document.querySelectorAll('.table-section').forEach(section => {
        let matches = 0;
        section.querySelectorAll('tbody tr').forEach(row => {
          const text = row.textContent.toLowerCase();
          const show = !term || text.includes(term);
          row.style.display = show ? '' : 'none';
          if (show) matches++;
        });
        const info = section.querySelector('.results-info');
        if (info) {
          info.textContent = term ? `Showing ${matches} matches` : '';
        }
        totalMatches += matches;
      });
      AdminEnhancements.showToast(`Found ${totalMatches} matches`, 'info');
    }
  
    function filterTables() {
      const selected = document.getElementById('tableFilter').value;
      document.querySelectorAll('.table-section').forEach(section => {
        section.style.display = (selected === 'all' || section.dataset.table === selected) ? '' : 'none';
      });
    }
  
    function filterTableByColumn() {
      document.querySelectorAll('.table-section').forEach(section => {
        const table = section.dataset.table;
        const rows = Array.from(section.querySelectorAll('tbody tr'));
        rows.forEach(row => {
          let show = true;
          section.querySelectorAll('.column-value-filter').forEach(sel => {
            if (sel.dataset.table === table) {
              const val = sel.value;
              const cell = row.querySelector(`td[data-column="${sel.dataset.column}"]`);
              if (val !== 'all' && cell && cell.textContent !== val) {
                show = false;
              }
            }
          });
          row.style.display = show ? '' : 'none';
        });
      });
    }
  
    function sortTable(tableName, column) {
      const section = document.querySelector(`.table-section[data-table="${tableName}"]`);
      if (!section) return;
      const tbody = section.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr')).filter(r => r.style.display !== 'none');
      const idx = Array.from(section.querySelectorAll('th')).findIndex(th => th.dataset.column === column);
      const asc = section.dataset.sortOrder !== 'asc';
      section.dataset.sortOrder = asc ? 'asc' : 'desc';
      rows.sort((a, b) => {
        const aVal = a.children[idx].textContent.trim();
        const bVal = b.children[idx].textContent.trim();
        const numA = parseFloat(aVal), numB = parseFloat(bVal);
        let cmp = isNaN(numA) || isNaN(numB) ? aVal.localeCompare(bVal) : numA - numB;
        return asc ? cmp : -cmp;
      });
      rows.forEach(r => tbody.appendChild(r));
      AdminEnhancements.showToast(`Sorted ${tableName} by ${column} (${asc ? 'asc' : 'desc'})`, 'info');
    }
  
    function exportTableData(tableName, format) {
      const section = document.querySelector(`.table-section[data-table="${tableName}"]`);
      if (!section) return;
      const rows = Array.from(section.querySelectorAll('tbody tr')).filter(r => r.style.display !== 'none');
      const data = rows.map(row => Array.from(row.children).map(td => td.textContent.trim()));
      let content, mime, ext;
      if (format === 'csv') {
        content = data.map(r => r.map(c => `"${c.replace(/"/g,'""')}"`).join(',')).join('\n');
        mime = 'text/csv'; ext = 'csv';
      } else {
        content = JSON.stringify(data); mime = 'application/json'; ext = 'json';
      }
      const blob = new Blob([content], { type: mime });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `${tableName}_export.${ext}`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
      AdminEnhancements.showToast(`Exported ${tableName} as ${ext}`, 'success');
    }

  /**
   * Initialize client-side pagination for each table section.
   */
  function initializeTablePagination() {
    document.querySelectorAll('.table-section').forEach(section => {
      const tableName = section.dataset.table;
      const rows = Array.from(section.querySelectorAll('tbody tr'));
      const perPageSelect = section.querySelector('.per-page-selector');
      const pagContainer = document.getElementById(`${tableName}PaginationControls`);
      if (!pagContainer) return;
      let currentPage = 1;

      function renderPage() {
        const perPage = perPageSelect ? parseInt(perPageSelect.value) : rows.length;
        const totalItems = rows.length;
        const totalPages = Math.ceil(totalItems / perPage);
        const start = (currentPage - 1) * perPage + 1;
        const end = Math.min(currentPage * perPage, totalItems);

        // Show/hide rows according to current page
        rows.forEach((row, idx) => {
          row.style.display = (idx >= start - 1 && idx < end) ? '' : 'none';
        });

        // Update results info
        const infoDiv = pagContainer.querySelector('.pagination-info');
        if (infoDiv) {
          infoDiv.textContent = `Viser ${start}-${end} av ${totalItems}`;
        }

        // Render page buttons inside the center container
        const buttonsWrapper = pagContainer.querySelector('.pagination-buttons');
        if (!buttonsWrapper) return;
        buttonsWrapper.innerHTML = '';

        // Previous button
        const prev = document.createElement('button');
        prev.className = 'page-btn';
        prev.disabled = currentPage === 1;
        prev.innerText = '‹ Forrige';
        prev.addEventListener('click', () => {
          if (currentPage > 1) {
            currentPage--;
            renderPage();
          }
        });
        buttonsWrapper.appendChild(prev);

        // Page buttons with ellipsis
        const pages = [];
        for (let i = 1; i <= totalPages; i++) {
          if (
            i === 1 ||
            i === totalPages ||
            (i >= currentPage - 2 && i <= currentPage + 2)
          ) {
            pages.push(i);
          } else if (pages[pages.length - 1] !== '…') {
            pages.push('…');
          }
        }
        pages.forEach(p => {
          if (p === '…') {
            const span = document.createElement('span');
            span.className = 'pagination-ellipsis';
            span.innerText = '…';
            buttonsWrapper.appendChild(span);
          } else {
            const btn = document.createElement('button');
            btn.className = 'page-btn' + (p === currentPage ? ' active' : '');
            btn.innerText = p;
            btn.addEventListener('click', () => {
              currentPage = p;
              renderPage();
            });
            buttonsWrapper.appendChild(btn);
          }
        });

        // Next button
        const next = document.createElement('button');
        next.className = 'page-btn';
        next.disabled = currentPage === totalPages;
        next.innerText = 'Neste ›';
        next.addEventListener('click', () => {
          if (currentPage < totalPages) {
            currentPage++;
            renderPage();
          }
        });
        buttonsWrapper.appendChild(next);
      }

      // Hook per-page changes
      if (perPageSelect) {
        perPageSelect.addEventListener('change', () => {
          currentPage = 1;
          renderPage();
        });
      }

      // Initial render
      renderPage();
    });
  }
  
  })(window, window.AdminEnhancements);