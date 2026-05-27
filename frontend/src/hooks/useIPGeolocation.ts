import { useCallback } from 'react';
import { useRaceFiltersStore } from '../store/raceFiltersStore';
import { isStateCode } from '../utils/usStates';

interface IpApiResponse {
  region_code?: string;
}

/**
 * Returns a `detectState` callback that — only when explicitly invoked —
 * calls ipapi.co to resolve the user's state from their IP address.
 * This is intentionally not called automatically to avoid transmitting the
 * user's IP to a third party without their consent.
 */
export const useIPGeolocation = () => {
  const setDetectedState = useRaceFiltersStore((state) => state.setDetectedState);

  const detectState = useCallback(() => {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 3000);

    void fetch('https://ipapi.co/json/', { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error('Unable to detect your state.');
        }
        return response.json() as Promise<IpApiResponse>;
      })
      .then((data) => {
        const stateCode = data.region_code?.toUpperCase();
        if (isStateCode(stateCode)) {
          setDetectedState(stateCode);
        }
      })
      .catch(() => undefined)
      .finally(() => {
        window.clearTimeout(timeoutId);
      });
  }, [setDetectedState]);

  return { detectState };
};
