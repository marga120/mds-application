import { api } from "../api/client.js";

export class StatusService {
  async getActiveStatuses() {
    const data = await api.get("/api/statuses");
    return data.statuses || [];
  }

  async getAllStatuses() {
    const data = await api.get("/api/admin/statuses");
    return data.statuses || [];
  }

  async createStatus(statusData) {
    return api.post("/api/admin/statuses", statusData);
  }

  async updateStatus(statusId, statusData) {
    return api.put(`/api/admin/statuses/${statusId}`, statusData);
  }

  async deleteStatus(statusId) {
    return api.delete(`/api/admin/statuses/${statusId}`);
  }

  async reorderStatuses(statuses) {
    return api.post("/api/admin/statuses/reorder", { statuses });
  }
}

export const statusService = new StatusService();
