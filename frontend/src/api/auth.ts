import type {
  AuthResponse,
  LoginPayload,
  ProfileUpdatePayload,
  RegisterPayload,
  UserProfile,
} from '../types';
import { apiClient } from './client';

export const authApi = {
  async login(payload: LoginPayload) {
    const response = await apiClient.post<AuthResponse>('/api/auth/login/', payload);
    return response.data;
  },
  async register(payload: RegisterPayload) {
    const response = await apiClient.post<AuthResponse>('/api/auth/register/', payload);
    return response.data;
  },
  async logout() {
    await apiClient.post('/api/auth/logout/');
  },
  async getProfile() {
    const response = await apiClient.get<UserProfile>('/api/users/me/profile/');
    return response.data;
  },
  async updateProfile(payload: ProfileUpdatePayload) {
    const response = await apiClient.patch<UserProfile>('/api/users/me/profile/', payload);
    return response.data;
  },
};
