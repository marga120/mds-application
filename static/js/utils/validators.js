/**
 * utils/validators.js
 * Pure validation functions.
 * All return { valid: boolean, message: string }.
 */

/**
 * Validates an email address.
 * @param {string} email
 * @returns {{ valid: boolean, message: string }}
 */
export function validateEmail(email) {
  if (!email || !email.trim()) {
    return { valid: false, message: "Email is required." };
  }
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!re.test(email.trim())) {
    return { valid: false, message: "Please enter a valid email address." };
  }
  return { valid: true, message: "" };
}

/**
 * Validates a password (minimum 8 characters).
 * @param {string} password
 * @returns {{ valid: boolean, message: string }}
 */
export function validatePassword(password) {
  if (!password) {
    return { valid: false, message: "Password is required." };
  }
  if (password.length < 8) {
    return { valid: false, message: "Password must be at least 8 characters." };
  }
  return { valid: true, message: "" };
}

/**
 * Validates that two passwords match.
 * @param {string} password
 * @param {string} confirmPassword
 * @returns {{ valid: boolean, message: string }}
 */
export function validateConfirmPassword(password, confirmPassword) {
  if (password !== confirmPassword) {
    return { valid: false, message: "Passwords do not match." };
  }
  return { valid: true, message: "" };
}

/**
 * Validates a rating value (optional, but if provided must be 0.0–10.0 with max 2 decimal places).
 * @param {string|number|null} value
 * @returns {{ valid: boolean, message: string }}
 */
export function validateRating(value) {
  if (value === null || value === undefined || value === "") {
    return { valid: true, message: "" };
  }
  const num = Number(value);
  if (isNaN(num)) {
    return { valid: false, message: "Rating must be a number." };
  }
  if (num < 0 || num > 10) {
    return { valid: false, message: "Rating must be between 0.0 and 10.0." };
  }
  if (!/^\d+(\.\d{1,2})?$/.test(String(value))) {
    return {
      valid: false,
      message: "Rating may have at most 2 decimal places.",
    };
  }
  return { valid: true, message: "" };
}

/**
 * Validates that a field is not empty.
 * @param {any} value
 * @param {string} fieldName
 * @returns {{ valid: boolean, message: string }}
 */
export function validateRequired(value, fieldName) {
  if (value === null || value === undefined || String(value).trim() === "") {
    return { valid: false, message: `${fieldName} is required.` };
  }
  return { valid: true, message: "" };
}

/**
 * Runs an array of validation results and returns the first failure,
 * or { valid: true, message: '' } if all pass.
 * @param {Array<{ valid: boolean, message: string }>} validators
 * @returns {{ valid: boolean, message: string }}
 */
export function validateAll(validators) {
  for (const result of validators) {
    if (!result.valid) return result;
  }
  return { valid: true, message: "" };
}
