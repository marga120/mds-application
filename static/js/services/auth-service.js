/**
 * services/auth-service.js
 * All auth-related API calls. No DOM manipulation.
 */
import { api } from "../api/client.js";

export class AuthService {
  async checkSession() {
    return api.get("/api/auth/check-session");
  }

  async getCurrentUser() {
    return api.get("/api/auth/user");
  }

  async login(email, password, remember = false) {
    return api.post("/api/auth/login", { email, password, remember });
  }

  async logout() {
    return api.post("/api/auth/logout", {});
  }

  async getUsers(searchQuery = "") {
    return api.get("/api/auth/users", searchQuery ? { q: searchQuery } : {});
  }

  async getUserById(id) {
    return api.get(`/api/auth/user/${id}`);
  }

  async createUser(data) {
    return api.post("/api/auth/register", data);
  }

  async updateUser(id, data) {
    return api.put(`/api/auth/user/${id}`, data);
  }

  async deleteUser(id) {
    return api.delete(`/api/auth/delete-user/${id}`);
  }

  async deleteUsers(ids) {
    return api.delete("/api/auth/delete-users", { user_ids: ids });
  }

  async updateEmail(newEmail, currentPassword) {
    return api.post("/api/auth/update-email", {
      new_email: newEmail,
      password: currentPassword,
    });
  }

  async resetPassword(currentPassword, newPassword) {
    return api.post("/api/auth/reset-password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }
}

export const authService = new AuthService();
