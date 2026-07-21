import axios, { AxiosHeaders } from 'axios';

let getAuthToken = () => null as string | null;
let handleUnauthorized = () => undefined;

export const registerAuthHandlers = (
  tokenGetter: () => string | null,
  unauthorizedHandler: () => void,
) => {
  getAuthToken = tokenGetter;
  handleUnauthorized = unauthorizedHandler;
};

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    ...(import.meta.env.VITE_CIVIC_API_KEY ? { 'X-Api-Key': import.meta.env.VITE_CIVIC_API_KEY } : {}),
  },
});

apiClient.interceptors.request.use((config) => {
  const token = getAuthToken();

  if (token) {
    const headers = AxiosHeaders.from(config.headers);
    headers.set('Authorization', `Token ${token}`);
    config.headers = headers;
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      handleUnauthorized();
    }

    return Promise.reject(error);
  },
);

const flattenErrorValue = (value: unknown): string | null => {
  if (typeof value === 'string') {
    return value;
  }

  if (Array.isArray(value)) {
    return value
      .map((entry) => flattenErrorValue(entry))
      .filter((entry): entry is string => Boolean(entry))
      .join(' ');
  }

  return null;
};

export const getApiFieldErrors = (error: unknown): Record<string, string> => {
  if (!axios.isAxiosError(error) || !error.response?.data || typeof error.response.data !== 'object') {
    return {};
  }

  const data = error.response.data as Record<string, unknown>;
  // The backend's custom_exception_handler wraps validation errors as
  // { detail, errors: { field: [...] }, status_code }. Prefer that nested
  // shape when present; fall back to a flat field-error dict otherwise.
  const fieldErrors =
    typeof data.errors === 'object' && data.errors ? (data.errors as Record<string, unknown>) : data;

  return Object.entries(fieldErrors).reduce<Record<string, string>>((accumulator, [key, value]) => {
    if (key === 'non_field_errors') {
      return accumulator;
    }
    const message = flattenErrorValue(value);
    if (message) {
      accumulator[key] = message;
    }
    return accumulator;
  }, {});
};

export const getApiErrorMessage = (error: unknown, fallback = 'Something went wrong.') => {
  if (!axios.isAxiosError(error)) {
    return fallback;
  }

  const data = error.response?.data;
  if (typeof data === 'object' && data) {
    const record = data as Record<string, unknown>;
    const nestedErrors =
      typeof record.errors === 'object' && record.errors ? (record.errors as Record<string, unknown>) : null;

    const nonFieldErrors = flattenErrorValue(nestedErrors?.non_field_errors ?? record.non_field_errors);
    if (nonFieldErrors) return nonFieldErrors;

    // Flatten all field errors (nested "errors" shape if present, else flat) into a readable message
    const fieldMessages = Object.entries(nestedErrors ?? record)
      .filter(([field]) => field !== 'non_field_errors' && field !== 'detail' && field !== 'status_code')
      .map(([field, value]) => {
        const msg = flattenErrorValue(value);
        return msg ? `${field}: ${msg}` : null;
      })
      .filter(Boolean)
      .join(' | ');
    if (fieldMessages) return fieldMessages;

    const detail = flattenErrorValue(record.detail);
    if (detail) return detail;
  }

  if (typeof data === 'string' && data) return data;

  return error.message || fallback;
};
