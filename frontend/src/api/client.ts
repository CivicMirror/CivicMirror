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

  return Object.entries(error.response.data as Record<string, unknown>).reduce<Record<string, string>>(
    (accumulator, [key, value]) => {
      const message = flattenErrorValue(value);
      if (message) {
        accumulator[key] = message;
      }
      return accumulator;
    },
    {},
  );
};

export const getApiErrorMessage = (error: unknown, fallback = 'Something went wrong.') => {
  if (!axios.isAxiosError(error)) {
    return fallback;
  }

  const data = error.response?.data;
  if (typeof data === 'object' && data) {
    const detail = flattenErrorValue((data as Record<string, unknown>).detail);
    if (detail) {
      return detail;
    }

    const nonFieldErrors = flattenErrorValue((data as Record<string, unknown>).non_field_errors);
    if (nonFieldErrors) {
      return nonFieldErrors;
    }
  }

  return error.message || fallback;
};
