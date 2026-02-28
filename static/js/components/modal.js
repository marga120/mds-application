/**
 * BaseModal — reusable modal component.
 *
 * Usage:
 *   const modal = new BaseModal({ onConfirm: () => doSomething() });
 *   modal.open('Title', '<p>Body HTML</p>');
 *   // ...later:
 *   modal.close();
 */
export class BaseModal {
  constructor(options = {}) {
    this._onConfirm = options.onConfirm || (() => {});
    this._onCancel = options.onCancel || (() => {});
    this._el = null;
  }

  _render(title, content) {
    return `
      <div id="baseModalOverlay" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div class="bg-white rounded-lg shadow-xl max-w-lg w-full">
          <div class="p-6">
            <div class="flex justify-between items-center mb-4">
              <h3 id="baseModalTitle" class="text-lg font-semibold text-gray-900">${title}</h3>
              <button id="baseModalClose" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>
            <div id="baseModalContent">${content}</div>
            <div id="baseModalActions" class="flex justify-end gap-3 mt-6">
              <button id="baseModalCancel" class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors">
                Cancel
              </button>
              <button id="baseModalConfirm" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                Confirm
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  open(title = "", content = "") {
    document.body.insertAdjacentHTML("beforeend", this._render(title, content));
    this._el = document.getElementById("baseModalOverlay");

    this._el
      .querySelector("#baseModalClose")
      .addEventListener("click", () => this.close());
    this._el.querySelector("#baseModalCancel").addEventListener("click", () => {
      this._onCancel();
      this.close();
    });
    this._el
      .querySelector("#baseModalConfirm")
      .addEventListener("click", () => this._onConfirm());

    return this;
  }

  close() {
    if (this._el) {
      this._el.remove();
      this._el = null;
    }
  }

  setTitle(title) {
    const el = this._el && this._el.querySelector("#baseModalTitle");
    if (el) el.textContent = title;
    return this;
  }

  setContent(html) {
    const el = this._el && this._el.querySelector("#baseModalContent");
    if (el) el.innerHTML = html;
    return this;
  }

  showLoading() {
    const actions = this._el && this._el.querySelector("#baseModalActions");
    if (actions) {
      actions.innerHTML =
        '<div class="flex justify-center"><div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div></div>';
    }
    return this;
  }

  showError(message) {
    const content = this._el && this._el.querySelector("#baseModalContent");
    if (content) {
      content.insertAdjacentHTML(
        "beforeend",
        `<p class="text-red-600 text-sm mt-3">${message}</p>`,
      );
    }
    return this;
  }

  destroy() {
    this.close();
  }
}
