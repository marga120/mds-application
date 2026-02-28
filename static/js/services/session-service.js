import { api } from "../api/client.js";

export class SessionService {
  async getSessions(includeArchived = false, campus = null) {
    const params = { include_archived: includeArchived };
    if (campus) params.campus = campus;
    const data = await api.get("/api/sessions", params);
    return data.sessions || {};
  }

  async getSessionById(id) {
    const data = await api.get(`/api/sessions/${id}`);
    return data.session;
  }

  async createSession(sessionData) {
    return api.post("/api/sessions/create", sessionData);
  }

  async archiveSession(id) {
    return api.put(`/api/sessions/${id}/archive`, {});
  }

  async restoreSession(id) {
    return api.put(`/api/sessions/${id}/restore`, {});
  }
}

export const sessionService = new SessionService();
