import { useEffect } from 'react';
import { LOCATION_STORAGE_KEY, useRaceFiltersStore } from '../store/raceFiltersStore';
import { isStateCode } from '../utils/usStates';

interface IpApiResponse {
  region_code?: string;
}

export const useIPGeolocation = () => {
  const scope = useRaceFiltersStore((state) => state.scope);
  const stateValue = useRaceFiltersStore((state) => state.state);
  const zip = useRaceFiltersStore((state) => state.zip);
  const address = useRaceFiltersStore((state) => state.address);
  const detectedState = useRaceFiltersStore((state) => state.detectedState);
  const setDetectedState = useRaceFiltersStore((state) => state.setDetectedState);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return undefined;
    }

    if (window.localStorage.getItem(LOCATION_STORAGE_KEY) || scope !== 'national' || stateValue || zip || address || detectedState) {
      return undefined;
    }

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

    return () => {
      window.clearTimeout(timeoutId);
      controller.abort();
    };
  }, [address, detectedState, scope, setDetectedState, stateValue, zip]);
};
