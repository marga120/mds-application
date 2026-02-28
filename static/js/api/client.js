/**
 * api/client.js
 * Centralized HTTP client. All fetch() calls go through this.
 * Never call fetch() directly in pages or services.
 */

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

class ApiClient {
  constructor() {
    this.BASE_URL = "";
  }

  async get(path, params = {}) {
    const url = this._buildUrl(path, params);
    return this._request("GET", url, {});
  }

  async post(path, body) {
    return this._request("POST", path, {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  async put(path, body) {
    return this._request("PUT", path, {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  async patch(path, body) {
    return this._request("PATCH", path, {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  async delete(path, body = {}) {
    return this._request("DELETE", path, {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  async upload(path, formData) {
    // No Content-Type header — browser sets multipart boundary automatically
    return this._request("POST", path, { body: formData });
  }

  _buildUrl(path, params) {
    if (!params || Object.keys(params).length === 0) return path;
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null),
    ).toString();
    return query ? `${path}?${query}` : path;
  }

  async _request(method, path, options) {
    const response = await fetch(this.BASE_URL + path, {
      method,
      credentials: "include",
      ...options,
    });
    return this._handleResponse(response);
  }

  async _handleResponse(response) {
    if (response.ok) {
      return response.json();
    }
    let message = `Request failed with status ${response.status}`;
    let data = null;
    try {
      data = await response.json();
      if (data && data.error) message = data.error;
      else if (data && data.message) message = data.message;
    } catch {
      // Response body not JSON — use default message
    }
    throw new ApiError(message, response.status, data);
  }
}

export const api = new ApiClient();
