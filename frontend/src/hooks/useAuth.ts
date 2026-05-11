import { useMemo } from 'react';
import { useAuthStore } from '../store/authStore';

export const useAuth = () => {
  const auth = useAuthStore((state) => ({
    token: state.token,
    user: state.user,
    profile: state.profile,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    isRestoring: state.isRestoring,
    login: state.login,
    register: state.register,
    logout: state.logout,
    setProfile: state.setProfile,
  }));

  return useMemo(
    () => ({
      ...auth,
      displayName: auth.user?.username ?? auth.profile?.username ?? 'Account',
    }),
    [auth],
  );
};
