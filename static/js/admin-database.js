/**
 * Database Section Enhancements
 * Handles multi-table search, filtering, sorting, column toggles, pagination, and export.
 */

// Use global toast notification function
function showToast(message, type = 'info') {
    // Try to use AdminUtils.showToast (from admin enhancements)
    if (typeof AdminUtils !== 'undefined' && typeof AdminUtils.showToast === 'function') {
        AdminUtils.showToast(message, type);
    } else if (typeof AdminEnhancements !== 'undefined' && AdminEnhancements.showToast) {
        AdminEnhancements.showToast(message, type);
    } else {
        // Fallback: create simple toast notification
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 10001;
            background: ${type === 'success' ? '#d4edda' : type === 'error' ? '#f8d7da' : '#d1ecf1'};
            color: ${type === 'success' ? '#155724' : type === 'error' ? '#721c24' : '#0c5460'};
            padding: 12px 20px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            max-width: 300px; font-size: 14px;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }
}

(function(window) {
    
    // Create namespace for database-specific filtering
    const DatabaseFiltering = {};
    
    /**
     * Initialize filtering for a specific table
     * @param {string} tableName - The table name to initialize
     */
    DatabaseFiltering.initializeTableFiltering = function(tableName) {
        // SCOPE CHECK: Only work within the database section
        const databaseSection = document.getElementById('databaseSection');
        if (!databaseSection) {
            console.log(`🚫 Database section not found - skipping table filtering for ${tableName}`);
            return;
        }
        
        // SCOPE ALL SELECTORS to only look within the database section
        const form = databaseSection.querySelector(`#filter-form-${tableName}`);
        const searchInput = form?.querySelector('.search-input');
        const columnFilters = form?.querySelectorAll('.column-value-filter');
        const searchBtn = form?.querySelector('.search-btn');
        const clearBtn = form?.querySelector('.clear-btn');
        const tableSection = databaseSection.querySelector(`.table-section[data-table="${tableName}"]`);
        const sortableHeaders = tableSection?.querySelectorAll('th.sortable');
        const table = databaseSection.querySelector(`#${tableName}-table`);
        
        if (!form || !tableSection) {
            console.log(`🚫 Required elements not found in database section for table ${tableName}`);
            return;
        }
        
        
        // AGGRESSIVE: Remove any existing AdminEnhancements listeners on this table
        if (table) {
            const newTable = table.cloneNode(true);
            table.parentNode.replaceChild(newTable, table);
        }
        
        // Re-get elements after cloning (still scoped to database section)
        const newTableSection = databaseSection.querySelector(`.table-section[data-table="${tableName}"]`);
        const newSortableHeaders = newTableSection?.querySelectorAll('th.sortable');
        
        // Prevent form submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
        });
        
        // Wire search input with debounce (dynamic filtering)
        if (searchInput) {
            let timeout;
            searchInput.addEventListener('input', (e) => {
                e.stopPropagation(); // Prevent event bubbling
                clearTimeout(timeout);
                timeout = setTimeout(() => DatabaseFiltering.applyFilters(tableName), 300);
            });
        }
        
        // Wire column filters for immediate filtering
        if (columnFilters) {
            columnFilters.forEach(select => {
                select.addEventListener('change', (e) => {
                    e.stopPropagation(); // Prevent event bubbling
                    DatabaseFiltering.applyFilters(tableName);
                });
            });
        }
        
        // Wire sorting headers (on the NEW table)
        if (newSortableHeaders) {
            newSortableHeaders.forEach(header => {
                header.addEventListener('click', (e) => {
                    e.stopPropagation(); // Prevent AdminEnhancements from also handling this event
                    e.preventDefault();   // Prevent any default behavior
                    const column = header.dataset.column;
                    if (column) {
                        sortTable(tableName, column);
                    }
                });
            });
        }
        
        // Hide search button since filtering is now automatic
        if (searchBtn) {
            searchBtn.style.display = 'none';
        }
        
        // Wire clear button
        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent event bubbling
                e.preventDefault();   // Prevent form submission
                DatabaseFiltering.clearFilters(tableName);
            });
        }
        
        // Initialize pagination
        initializeTablePagination(tableName);
    };
    
    
    /**
     * Apply all filters for a specific table
     * @param {string} tableName - The table to filter
     */
    DatabaseFiltering.applyFilters = function(tableName) {
        // SCOPE CHECK: Only work within the database section
        const databaseSection = document.getElementById('databaseSection');
        if (!databaseSection) {
            console.log(`🚫 Database section not found - skipping filtering for ${tableName}`);
            return;
        }
        
        
        // SCOPE ALL SELECTORS to database section
        const form = databaseSection.querySelector(`#filter-form-${tableName}`);
        const tableSection = databaseSection.querySelector(`.table-section[data-table="${tableName}"]`);
        const rows = tableSection?.querySelectorAll('tbody tr');
        
        if (!form || !rows) {
            console.log(`🚫 Required elements not found for filtering table ${tableName}`);
            return;
        }
        
        const searchTerm = form.querySelector('.search-input')?.value.trim().toLowerCase() || '';
        const columnFilters = {};
        
        // Collect column filter values
        form.querySelectorAll('.column-value-filter').forEach(select => {
            const column = select.dataset.column;
            const value = select.value;
            if (value !== 'all') {
                columnFilters[column] = value;
            }
        });
        
        // Apply filters to rows
        rows.forEach(row => {
            let showRow = true;
            
            // Apply search filter
            if (searchTerm) {
                const rowText = row.textContent.toLowerCase();
                if (!rowText.includes(searchTerm)) {
                    showRow = false;
                }
            }
            
            // Apply column filters
            if (showRow) {
                for (const [column, filterValue] of Object.entries(columnFilters)) {
                    const cell = row.querySelector(`td[data-column="${column}"]`);
                    if (cell && cell.textContent.trim() !== filterValue) {
                        showRow = false;
                        break;
                    }
                }
            }
            
            // Use data attribute instead of direct style manipulation
            if (showRow) {
                row.removeAttribute('data-filtered-out');
            } else {
                row.setAttribute('data-filtered-out', 'true');
            }
        });
        
        // Reset pagination to page 1 after filtering and trigger re-render
        const section = document.querySelector(`.table-section[data-table="${tableName}"]`);
        if (section && section._paginationRender) {
            section._currentPage = 1;
            section._paginationRender();
        }
    };
    
    
    /**
     * Clear all filters for a specific table
     * @param {string} tableName - The table to clear filters for
     */
    DatabaseFiltering.clearFilters = function(tableName) {
        // SCOPE CHECK: Only work within the database section
        const databaseSection = document.getElementById('databaseSection');
        if (!databaseSection) {
            console.log(`🚫 Database section not found - skipping clear for ${tableName}`);
            return;
        }
        
        console.log(`🗑️ Clearing database filters for table: ${tableName}`);
        
        // SCOPE ALL SELECTORS to database section
        const form = databaseSection.querySelector(`#filter-form-${tableName}`);
        if (!form) {
            console.log(`🚫 Form not found for clearing table ${tableName}`);
            return;
        }
        
        // Clear search input
        const searchInput = form.querySelector('.search-input');
        if (searchInput) searchInput.value = '';
        
        // Reset column filters
        form.querySelectorAll('.column-value-filter').forEach(select => {
            select.value = 'all';
        });
        
        // Apply cleared filters
        DatabaseFiltering.applyFilters(tableName);
    };
    
    

  
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
  

  

  
    function initializeExportButtons() {
      document.querySelectorAll('[data-export]').forEach(btn => {
        btn.addEventListener('click', () => {
          const tableName = btn.dataset.table;
          const format = btn.dataset.format;
          exportTableData(tableName, format);
        });
      });
    }
  
    // Initial setup for remaining features (not handled by DatabaseFiltering)
    document.addEventListener('DOMContentLoaded', () => {
      initializeColumnToggles();
      initializeExportButtons();
      // Note: Table pagination, sorting, and filtering are now handled by DatabaseFiltering.initializeTableFiltering()
    });
  
  
    // Functions (reusing AdminEnhancements.showToast for notifications)
  
    function filterTables() {
      const selected = document.getElementById('tableFilter').value;
      document.querySelectorAll('.table-section').forEach(section => {
        section.style.display = (selected === 'all' || section.dataset.table === selected) ? '' : 'none';
      });
    }
  

  
    function sortTable(tableName, column) {
      const section = document.querySelector(`.table-section[data-table="${tableName}"]`);
      if (!section) return;
      const tbody = section.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr')).filter(r => r.style.display !== 'none');
      const header = section.querySelector(`th[data-column="${column}"]`);
      const sortIndicator = header?.querySelector('.sort-indicator');
      const idx = Array.from(section.querySelectorAll('th')).findIndex(th => th.dataset.column === column);
      
      // Clear all other sort indicators in this table
      section.querySelectorAll('.sort-indicator').forEach(indicator => {
        if (indicator !== sortIndicator) {
          indicator.className = 'sort-indicator';
        }
      });
      
      // Determine sort order
      const currentOrder = sortIndicator?.classList.contains('asc') ? 'asc' : 
                          sortIndicator?.classList.contains('desc') ? 'desc' : 'none';
      const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
      
      // Update sort indicator
      if (sortIndicator) {
        sortIndicator.className = `sort-indicator ${newOrder}`;
      }
      
      rows.sort((a, b) => {
        const aVal = a.children[idx].textContent.trim();
        const bVal = b.children[idx].textContent.trim();
        const numA = parseFloat(aVal), numB = parseFloat(bVal);
        let cmp = isNaN(numA) || isNaN(numB) ? aVal.localeCompare(bVal) : numA - numB;
        return newOrder === 'asc' ? cmp : -cmp;
      });
      
      rows.forEach(r => tbody.appendChild(r));
      
      // Show toast notification (safe fallback)
      if (typeof showToast === 'function') {
        showToast(`Sorted ${tableName} by ${column} (${newOrder === 'asc' ? 'ascending' : 'descending'})`, 'info');
      } else {
        console.log(`Sorted ${tableName} by ${column} (${newOrder === 'asc' ? 'ascending' : 'descending'})`);
      }
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
      
      // Show toast notification (safe fallback)
      if (typeof showToast === 'function') {
        showToast(`Exported ${tableName} as ${ext}`, 'success');
      } else {
        console.log(`Exported ${tableName} as ${ext}`);
      }
    }

  /**
   * Initialize client-side pagination for a specific table.
   * @param {string} tableName - The table name to initialize pagination for
   */
  function initializeTablePagination(tableName) {
    const section = document.querySelector(`.table-section[data-table="${tableName}"]`);
    const rows = Array.from(section.querySelectorAll('tbody tr'));
    const pagContainer = document.getElementById(`${tableName}PaginationControls`);
    const perPageSelect = pagContainer ? pagContainer.querySelector('.per-page-selector') : null;
    if (!pagContainer) return;
    let currentPage = 1;
    
    // Store pagination function on section for external access
    section._currentPage = currentPage;
    section._paginationRender = renderPage;

    function renderPage() {
      const perPage = perPageSelect ? parseInt(perPageSelect.value) : rows.length;
      // Get rows that are not filtered out (but ignore pagination hiding)
      const visibleRows = rows.filter(row => !row.hasAttribute('data-filtered-out'));
      const totalItems = visibleRows.length;
      const totalPages = perPage === 'all' || isNaN(perPage) ? 1 : Math.ceil(totalItems / perPage);
      const start = (currentPage - 1) * perPage + 1;
      const end = perPage === 'all' || isNaN(perPage) ? totalItems : Math.min(currentPage * perPage, totalItems);

      // First, show all visible rows, then hide pagination-excluded ones
      rows.forEach(row => {
        if (row.hasAttribute('data-filtered-out')) {
          row.style.display = 'none';
        } else {
          row.style.display = '';
        }
      });

      // Then apply pagination hiding
      if (perPage !== 'all' && !isNaN(perPage)) {
        visibleRows.forEach((row, idx) => {
          if (idx < start - 1 || idx >= end) {
            row.style.display = 'none';
          }
        });
      }

      // Update results info
      const infoDiv = pagContainer.querySelector('.pagination-info');
      if (infoDiv) {
        if (perPage === 'all' || isNaN(perPage)) {
          infoDiv.textContent = `Viser alle ${totalItems} elementer`;
        } else {
          infoDiv.textContent = `Viser ${start}-${end} av ${totalItems} elementer`;
        }
      }

      // Render page buttons inside the center container
      const buttonsWrapper = pagContainer.querySelector('.pagination-buttons');
      if (!buttonsWrapper) return;
      buttonsWrapper.innerHTML = '';

      if (totalPages <= 1) return; // Don't show pagination for single page

      // Previous button
      const prev = document.createElement('button');
      prev.className = 'page-btn';
      if (currentPage === 1) {
        prev.disabled = true;
        prev.classList.add('disabled');
      }
      prev.innerHTML = '<span class="pagination-arrow">‹</span> Forrige';
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
      if (currentPage === totalPages) {
        next.disabled = true;
        next.classList.add('disabled');
      }
      next.innerHTML = 'Neste <span class="pagination-arrow">›</span>';
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
  }
  
  // Database Control Features
  DatabaseFiltering.initializeDatabaseControls = function() {
  
  // Initialize multiselect dropdown
  DatabaseFiltering.initializeMultiselectDropdown();
  
  // Initialize table visibility toggles
  const visibilityCheckboxes = document.querySelectorAll('.table-visibility-checkbox');
  visibilityCheckboxes.forEach(checkbox => {
  checkbox.addEventListener('change', function() {
  const tableName = this.dataset.table;
  const tableSection = document.querySelector(`.table-section[data-table="${tableName}"]`);
  const paginationControls = document.getElementById(`${tableName}PaginationControls`);
  if (tableSection) {
  tableSection.style.display = this.checked ? '' : 'none';
  }
  if (paginationControls) {
      paginationControls.style.display = this.checked ? '' : 'none';
      }
          DatabaseFiltering.saveTableVisibilityPreferences();
          DatabaseFiltering.updateVisibilityStatus();
          DatabaseFiltering.updateDropdownSelectedText();
      });
  });
  
  // Initialize select all / deselect all buttons
  const selectAllBtn = document.getElementById('selectAllTables');
  const deselectAllBtn = document.getElementById('deselectAllTables');
  
  if (selectAllBtn) {
      selectAllBtn.addEventListener('click', function() {
          const checkboxes = document.querySelectorAll('.table-visibility-checkbox');
          checkboxes.forEach(cb => {
              if (!cb.checked) {
                  cb.checked = true;
                      cb.dispatchEvent(new Event('change'));
                    }
                });
            });
        }
        
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', function() {
                const checkboxes = document.querySelectorAll('.table-visibility-checkbox');
                checkboxes.forEach(cb => {
                    if (cb.checked) {
                        cb.checked = false;
                        cb.dispatchEvent(new Event('change'));
                    }
                });
            });
        }
        
        // Initialize table display mode selector
        const densitySelector = document.getElementById('tableDensitySelector');
        if (densitySelector) {
            densitySelector.addEventListener('change', function() {
                DatabaseFiltering.applyTableDisplayMode(this.value);
                DatabaseFiltering.saveDisplayModePreference(this.value);
            });
        }
        
        // Load saved preferences
        DatabaseFiltering.loadSavedPreferences();
        
        // Update initial visibility status
        DatabaseFiltering.updateVisibilityStatus();
        DatabaseFiltering.updateDropdownSelectedText();
    };
    
    DatabaseFiltering.applyTableDisplayMode = function(mode) {
        const tables = document.querySelectorAll('.database-table');
        tables.forEach(table => {
            // Remove existing mode classes
            table.classList.remove('compact', 'airy', 'comfortable');
            // Add new mode class
            table.classList.add(mode);
        });
    };
    
    DatabaseFiltering.saveTableVisibilityPreferences = function() {
        const preferences = {};
        const checkboxes = document.querySelectorAll('.table-visibility-checkbox');
        checkboxes.forEach(checkbox => {
            preferences[checkbox.dataset.table] = checkbox.checked;
        });
        localStorage.setItem('database_table_visibility', JSON.stringify(preferences));
    };
    
    DatabaseFiltering.saveDisplayModePreference = function(mode) {
        localStorage.setItem('database_display_mode', mode);
    };
    
    DatabaseFiltering.updateVisibilityStatus = function() {
        const checkboxes = document.querySelectorAll('.table-visibility-checkbox');
        const total = checkboxes.length;
        const visible = Array.from(checkboxes).filter(cb => cb.checked).length;
        const statusElement = document.getElementById('visibilityStatus');
        
        if (statusElement) {
            if (visible === total) {
                statusElement.textContent = 'Viser alle tabeller';
                statusElement.style.color = '#64748b';
            } else if (visible === 0) {
                statusElement.textContent = 'Ingen tabeller synlige';
                statusElement.style.color = '#ef4444';
            } else {
                statusElement.textContent = `Viser ${visible} av ${total} tabeller`;
                statusElement.style.color = '#f59e0b';
            }
        }
    };
    
    DatabaseFiltering.initializeMultiselectDropdown = function() {
        
        
        const dropdown = document.getElementById('tableVisibilityDropdown');
        const selected = document.getElementById('tableVisibilitySelected');
        const options = document.getElementById('tableVisibilityOptions');
        // GUARD: Prevent duplicate initialization 
        if (selected && selected.dataset.dropdownInitialized === 'true') {
            return;
        }
        
        if (!dropdown || !selected || !options) {
            console.warn('⚠️ Multiselect dropdown elements not found');
            return;
        }
        
        
        // Ensure dropdown starts closed
        dropdown.classList.remove('open');
        options.style.display = 'none';
        
        // Track if we're currently in a toggle operation to prevent immediate closing
        let isToggling = false;
        
        function toggleDropdown(e) {
            
            e.preventDefault();
            e.stopPropagation();
            
            // Set toggling flag to prevent document click from immediately closing
            isToggling = true;
            
            const isOpen = dropdown.classList.contains('open');

            
            if (isOpen) {
                dropdown.classList.remove('open');
                options.style.display = 'none';
            } else {
                dropdown.classList.add('open');
                options.style.display = 'flex';
                options.style.flexDirection = 'column';
            }
            
            // Reset the toggling flag after a brief delay
            setTimeout(() => {
                isToggling = false;
            }, 100); // Increased delay to 100ms
        }
        
        // Debug: Add listener to track all clicks on the document
        document.addEventListener('click', function(e) {
            if (dropdown.contains(e.target)) {
            }
        }, true); // Use capture phase
        
        // Bind single click event to the selected element only
        selected.addEventListener('click', function(e) {
            // Prevent event bubbling to avoid double-firing
            e.stopPropagation();
            toggleDropdown(e);
        });
        
        // Close dropdown when clicking outside - but only if not currently toggling
        document.addEventListener('click', function(e) {
            
            if (!isToggling && !dropdown.contains(e.target) && !e.target.closest('.btn[onclick*="showSection"]')) {
                if (dropdown.classList.contains('open')) {
                    dropdown.classList.remove('open');
                    options.style.display = 'none';
                }
            } else {
            }
        });
        
        // Prevent dropdown from closing when clicking inside options
        options.addEventListener('click', function(e) {
            e.stopPropagation();
        });

        if (selected) {
            selected.dataset.dropdownInitialized = 'true';
        }
        
    };
    
    DatabaseFiltering.updateDropdownSelectedText = function() {
        const checkboxes = document.querySelectorAll('.table-visibility-checkbox');
        const selectedText = document.querySelector('.selected-text');
        
        if (!selectedText) {
            console.warn('⚠️ Selected text element not found');
            return;
        }
        
        const checkedBoxes = Array.from(checkboxes).filter(cb => cb.checked);
        const total = checkboxes.length;
        
        if (checkedBoxes.length === 0) {
            selectedText.textContent = 'Ingen tabeller valgt';
        } else if (checkedBoxes.length === total) {
            selectedText.textContent = 'Alle tabeller valgt';
        } else if (checkedBoxes.length === 1) {
            const tableName = checkedBoxes[0].dataset.table.replace(/_/g, ' ').toUpperCase();
            selectedText.textContent = tableName;
        } else {
            selectedText.textContent = `${checkedBoxes.length} tabeller valgt`;
        }
        
    };
    
    DatabaseFiltering.loadSavedPreferences = function() {
        // Load table visibility preferences
        const savedVisibility = localStorage.getItem('database_table_visibility');
        if (savedVisibility) {
            try {
                const preferences = JSON.parse(savedVisibility);
                Object.entries(preferences).forEach(([tableName, isVisible]) => {
                    const checkbox = document.querySelector(`.table-visibility-checkbox[data-table="${tableName}"]`);
                    const tableSection = document.querySelector(`.table-section[data-table="${tableName}"]`);
                    const paginationControls = document.getElementById(`${tableName}PaginationControls`);
                    if (checkbox && tableSection) {
                        checkbox.checked = isVisible;
                        tableSection.style.display = isVisible ? '' : 'none';
                    }
                    if (paginationControls) {
                        paginationControls.style.display = isVisible ? '' : 'none';
                    }
                });
                DatabaseFiltering.updateVisibilityStatus();
                DatabaseFiltering.updateDropdownSelectedText();
            } catch (e) {
                console.warn('⚠️ Failed to load table visibility preferences:', e);
            }
        }
        
        // Load display mode preference
        const savedMode = localStorage.getItem('database_display_mode');
        if (savedMode) {
            const densitySelector = document.getElementById('tableDensitySelector');
            if (densitySelector) {
                densitySelector.value = savedMode;
                DatabaseFiltering.applyTableDisplayMode(savedMode);
            }
        } else {
            // Default to comfortable mode
            DatabaseFiltering.applyTableDisplayMode('comfortable');
        }
    };
    
    // Expose DatabaseFiltering globally
    window.DatabaseFiltering = DatabaseFiltering;
  
  })(window);