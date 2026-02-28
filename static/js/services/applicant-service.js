import { api } from "../api/client.js";

export class ApplicantService {
  async getApplicants(sessionId = null) {
    const params = sessionId ? { session_id: sessionId } : {};
    const result = await api.get("/api/applicants", params);
    return result.applicants || [];
  }

  async getApplicantInfo(userCode) {
    const result = await api.get(`/api/applicant-info/${userCode}`);
    return result.applicant || null;
  }

  async getApplicationInfo(userCode) {
    const result = await api.get(`/api/applicant-application-info/${userCode}`);
    return result.application_info || null;
  }

  async getTestScores(userCode) {
    const result = await api.get(`/api/applicant-test-scores/${userCode}`);
    return result.test_scores || {};
  }

  async getInstitutions(userCode) {
    const result = await api.get(`/api/applicant-institutions/${userCode}`);
    return result.institutions || [];
  }

  async updateStatus(userCode, status) {
    return api.put(`/api/applicant-application-info/${userCode}/status`, {
      status,
    });
  }

  async updatePrerequisites(userCode, data) {
    return api.put(
      `/api/applicant-application-info/${userCode}/prerequisites`,
      data,
    );
  }

  async updateEnglishComment(userCode, comment) {
    return api.put(
      `/api/applicant-application-info/${userCode}/english-comment`,
      {
        english_comment: comment,
      },
    );
  }

  async updateEnglishStatus(userCode, status) {
    return api.put(
      `/api/applicant-application-info/${userCode}/english-status`,
      {
        english_status: status,
      },
    );
  }

  async updateScholarship(userCode, scholarship) {
    return api.put(`/api/applicant-application-info/${userCode}/scholarship`, {
      scholarship,
    });
  }

  async uploadCSV(file) {
    const formData = new FormData();
    formData.append("file", file);
    return api.upload("/api/upload", formData);
  }

  async exportAll(sessionId = null) {
    const params = sessionId ? `?session_id=${sessionId}` : "";
    window.location.href = `/api/export/all${params}`;
  }

  async exportSelected(userCodes, sections = null) {
    return api.post("/api/export/selected", {
      user_codes: userCodes,
      sections,
    });
  }

  async clearAllData() {
    return api.delete("/api/clear-all-data");
  }
}

export const applicantService = new ApplicantService();
