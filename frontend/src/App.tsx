import { useEffect, useRef } from 'react';
import { Route, Routes } from 'react-router-dom';
import ProtectedRoute from './components/common/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';
import CoveragePage from './pages/CoveragePage';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import ProfilePage from './pages/ProfilePage';
import RaceDetailPage from './pages/RaceDetailPage';
import RaceSubmitPage from './pages/RaceSubmitPage';
import RegisterPage from './pages/RegisterPage';
import { useAuthStore } from './store/authStore';

function App() {
  const restoreFromStorage = useAuthStore((state) => state.restoreFromStorage);
  const hasBootstrapped = useRef(false);

  useEffect(() => {
    if (hasBootstrapped.current) {
      return;
    }

    hasBootstrapped.current = true;
    restoreFromStorage();
  }, [restoreFromStorage]);

  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/coverage" element={<CoveragePage />} />
        <Route
          path="/races/submit"
          element={
            <ProtectedRoute>
              <RaceSubmitPage />
            </ProtectedRoute>
          }
        />
        <Route path="/races/:id" element={<RaceDetailPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />
      </Route>
    </Routes>
  );
}

export default App;
