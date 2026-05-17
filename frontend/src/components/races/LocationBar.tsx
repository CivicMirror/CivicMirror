import type * as React from 'react';
import MyLocation from '@mui/icons-material/MyLocation';
import TravelExplore from '@mui/icons-material/TravelExplore';
import {
  Alert,
  Box,
  Button,
  Chip,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { useRaceFiltersStore, type RaceFilterScope } from '../../store/raceFiltersStore';
import { formatStateName } from '../../utils/format';
import { US_STATES } from '../../utils/usStates';
import ContestTypeFilter from './ContestTypeFilter';

interface LocationBarProps {
  resolvedScope: RaceFilterScope;
  effectiveState: string | null;
  zip: string | null;
  address: string | null;
  activeLocationLabel: string | null;
  isAutoDetected: boolean;
}

function LocationBar({
  resolvedScope,
  effectiveState,
  zip,
  address,
  activeLocationLabel,
  isAutoDetected,
}: LocationBarProps) {
  const setScope = useRaceFiltersStore((state) => state.setScope);
  const setState = useRaceFiltersStore((state) => state.setState);
  const setZip = useRaceFiltersStore((state) => state.setZip);
  const setAddress = useRaceFiltersStore((state) => state.setAddress);
  const clearLocationPreference = useRaceFiltersStore((state) => state.clearLocationPreference);

  const [zipInput, setZipInput] = useState(zip ?? '');
  const [addressInput, setAddressInput] = useState(address ?? '');
  const [zipError, setZipError] = useState<string | null>(null);
  const [addressError, setAddressError] = useState<string | null>(null);

  useEffect(() => {
    setZipInput(zip ?? '');
  }, [zip]);

  useEffect(() => {
    setAddressInput(address ?? '');
  }, [address]);

  const chipLabel = useMemo(() => {
    if (!activeLocationLabel) {
      return null;
    }

    if (resolvedScope === 'state') {
      return `Showing races in ${formatStateName(activeLocationLabel)}`;
    }

    if (resolvedScope === 'zip') {
      return `Showing races near ZIP ${activeLocationLabel}`;
    }

    return `Showing races near ${activeLocationLabel}`;
  }, [activeLocationLabel, resolvedScope]);

  const handleTabChange = (_event: React.SyntheticEvent, nextScope: RaceFilterScope) => {
    setZipError(null);
    setAddressError(null);

    if (nextScope === 'national') {
      clearLocationPreference();
      return;
    }

    setScope(nextScope);
  };

  const handleZipSubmit = () => {
    if (!/^\d{5}$/.test(zipInput.trim())) {
      setZipError('Enter a valid 5-digit ZIP code.');
      return;
    }

    setZipError(null);
    setZip(zipInput.trim());
  };

  const handleAddressSubmit = () => {
    if (!addressInput.trim()) {
      setAddressError('Enter a street address, city, or full mailing address.');
      return;
    }

    setAddressError(null);
    setAddress(addressInput.trim());
  };

  return (
    <Stack id="civicmirror-location-bar" spacing={2.5}>
      <Box>
        <Typography gutterBottom variant="h5">
          Find races near you
        </Typography>
        <Typography color="text.secondary">
          Public browsing always works. Add a location to move from a national feed to statewide
          and local contests.
        </Typography>
      </Box>

      {chipLabel ? (
        <Stack alignItems="center" direction="row" flexWrap="wrap" gap={1}>
          <Chip
            color={isAutoDetected ? 'secondary' : 'primary'}
            icon={isAutoDetected ? <MyLocation /> : <TravelExplore />}
            label={chipLabel}
            onDelete={() => {
              clearLocationPreference();
            }}
          />
          <Button
            onClick={() => {
              document.getElementById('civicmirror-location-bar')?.scrollIntoView({
                behavior: 'smooth',
                block: 'center',
              });
            }}
            size="small"
          >
            Change
          </Button>
        </Stack>
      ) : null}

      <Box bgcolor="background.paper" borderRadius={3} p={{ xs: 2, md: 3 }}>
        <Stack spacing={2}>
          <Tabs onChange={handleTabChange} scrollButtons="auto" value={resolvedScope} variant="scrollable">
            <Tab label="National" value="national" />
            <Tab label="State" value="state" />
            <Tab label="ZIP" value="zip" />
            <Tab label="Address" value="address" />
          </Tabs>

          {resolvedScope === 'state' ? (
            <FormControl fullWidth>
              <InputLabel id="state-select-label">State</InputLabel>
              <Select
                label="State"
                labelId="state-select-label"
                onChange={(event) => {
                  setState(event.target.value);
                }}
                value={effectiveState ?? ''}
              >
                {US_STATES.map((stateOption) => (
                  <MenuItem key={stateOption.code} value={stateOption.code}>
                    {stateOption.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          ) : null}

          {resolvedScope === 'zip' ? (
            <Stack direction={{ xs: 'column', sm: 'row' }} gap={1.5}>
              <TextField
                error={Boolean(zipError)}
                fullWidth
                helperText={zipError ?? 'ZIP lookups approximate local ballots because Civic data is address-based.'}
                inputProps={{ inputMode: 'numeric', maxLength: 5 }}
                label="ZIP code"
                onChange={(event) => {
                  setZipInput(event.target.value.replace(/[^0-9]/g, ''));
                  setZipError(null);
                }}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    event.preventDefault();
                    handleZipSubmit();
                  }
                }}
                value={zipInput}
              />
              <Button onClick={handleZipSubmit} sx={{ minWidth: 120 }} variant="contained">
                Apply
              </Button>
            </Stack>
          ) : null}

          {resolvedScope === 'address' ? (
            <Stack direction={{ xs: 'column', sm: 'row' }} gap={1.5}>
              <TextField
                error={Boolean(addressError)}
                fullWidth
                helperText={
                  addressError ??
                  'Addresses are kept in your browser to restore your view and should never be stored permanently server-side.'
                }
                label="Street address"
                onChange={(event) => {
                  setAddressInput(event.target.value);
                  setAddressError(null);
                }}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    event.preventDefault();
                    handleAddressSubmit();
                  }
                }}
                placeholder="1600 Pennsylvania Ave NW, Washington, DC"
                value={addressInput}
              />
              <Button onClick={handleAddressSubmit} sx={{ minWidth: 120 }} variant="contained">
                Search
              </Button>
            </Stack>
          ) : null}
        </Stack>
      </Box>

      <ContestTypeFilter />

      {isAutoDetected ? (
        <Alert severity="info">We auto-detected your state from IP geolocation. Change it anytime.</Alert>
      ) : null}
    </Stack>
  );
}

export default LocationBar;
