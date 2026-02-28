/**
 * DataTable — sortable table helper.
 *
 * Usage:
 *   const dt = new DataTable(document.querySelector('table'), {
 *     sortable: true,
 *     onSort: (col, dir) => reloadData(col, dir),
 *   });
 *   dt.updateSortIndicators('name', 'asc');
 *
 * Add data-sort="fieldName" to <th> elements to make them sortable.
 * Add <span class="sort-icon"></span> inside each sortable <th> for indicators.
 */
export class DataTable {
  constructor(tableEl, options = {}) {
    this._table = tableEl;
    this._sortable = options.sortable !== false;
    this._onSort = options.onSort || null;
    this._sortCol = null;
    this._sortDir = "asc";

    if (this._sortable && this._table) {
      this._bindHeaders();
    }
  }

  _bindHeaders() {
    const headers = this._table.querySelectorAll("th[data-sort]");
    headers.forEach((th) => {
      th.classList.add("cursor-pointer", "select-none");
      th.addEventListener("click", () => {
        const col = th.dataset.sort;
        if (this._sortCol === col) {
          this._sortDir = this._sortDir === "asc" ? "desc" : "asc";
        } else {
          this._sortCol = col;
          this._sortDir = "asc";
        }
        this.updateSortIndicators(this._sortCol, this._sortDir);
        if (this._onSort) this._onSort(this._sortCol, this._sortDir);
      });
    });
  }

  sort(column, direction) {
    this._sortCol = column;
    this._sortDir = direction;
    this.updateSortIndicators(column, direction);
  }

  updateSortIndicators(column, direction) {
    if (!this._table) return;
    const headers = this._table.querySelectorAll("th[data-sort]");
    headers.forEach((th) => {
      const icon = th.querySelector(".sort-icon");
      if (!icon) return;
      if (th.dataset.sort === column) {
        icon.textContent = direction === "asc" ? " ↑" : " ↓";
      } else {
        icon.textContent = " ↕";
      }
    });
  }
}
