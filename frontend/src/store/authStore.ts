import { create } from 'zustand';
import { authApi } from '../api/auth';
import { registerAuthHandlers } from '../api/client';
import type { LoginPayload, RegisterPayload, User, UserProfile } from '../types';

const TOKEN_STORAGE_KEY = 'civicmirror_token';

interface AuthState {
  token: string | null;
  user: User | null;
  profile: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isRestoring: boolean;
  login: (credentials: LoginPayload) => Promise<void>;
  register: (data: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  clearAuth: () => void;
  restoreFromStorage: () => void;
  setProfile: (profile: UserProfile) => void;
}

const persistToken = (token: string) => {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
};

const clearPersistedToken = () => {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
};

const initialToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
let hasStartedRestore = false;

export const useAuthStore = create<AuthState>((set, get) => ({
  token: initialToken,
  user: null,
  profile: null,
  isAuthenticated: Boolean(initialToken),
  isLoading: false,
  isRestoring: Boolean(initialToken),
  async login(credentials) {
    set({ isLoading: true });
    try {
      const response = await authApi.login(credentials);
      persistToken(response.token);
      set({
        token: response.token,
        user: response.user,
        profile: response.profile,
        isAuthenticated: true,
        isLoading: false,
        isRestoring: false,
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
  async register(data) {
    set({ isLoading: true });
    try {
      const response = await authApi.register(data);
      persistToken(response.token);
      set({
        token: response.token,
        user: response.user,
        profile: response.profile,
        isAuthenticated: true,
        isLoading: false,
        isRestoring: false,
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
  async logout() {
    set({ isLoading: true });
    try {
      await authApi.logout();
    } finally {
      get().clearAuth();
    }
  },
  clearAuth() {
    clearPersistedToken();
    set({
      token: null,
      user: null,
      profile: null,
      isAuthenticated: false,
      isLoading: false,
      isRestoring: false,
    });
  },
  restoreFromStorage() {
    if (hasStartedRestore) {
      return;
    }
    hasStartedRestore = true;

    const token = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      set({ isRestoring: false });
      return;
    }

    set({ token, isAuthenticated: true, isRestoring: true });

    void authApi
      .getProfile()
      .then((profile) => {
        set((state) => ({
          profile,
          user: state.user ? { ...state.user, username: profile.username } : state.user,
          isAuthenticated: true,
        }));
      })
      .catch(() => {
        get().clearAuth();
      })
      .finally(() => {
        set({ isRestoring: false });
      });
  },
  setProfile(profile) {
    set((state) => ({
      profile,
      user: state.user ? { ...state.user, username: profile.username } : state.user,
    }));
  },
}));

registerAuthHandlers(
  () => useAuthStore.getState().token,
  () => useAuthStore.getState().clearAuth(),
);
