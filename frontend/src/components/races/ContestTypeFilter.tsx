import { Chip, Stack, Typography } from '@mui/material';
import { useRaceFiltersStore } from '../../store/raceFiltersStore';

const PRIMARY_OPTIONS = [
  { value: null, label: 'All' },
  { value: 'candidate', label: 'Elections' },
  { value: 'measure', label: 'Ballot Measures' },
] as const;

const ELECTION_SUB_TYPES = [
  { value: 'General', label: 'General' },
  { value: 'Primary', label: 'Primary' },
  { value: 'Run-off', label: 'Run-off' },
  { value: 'Retention', label: 'Retention' },
] as const;

function ContestTypeFilter() {
  const contestType = useRaceFiltersStore((s) => s.contestType);
  const setContestType = useRaceFiltersStore((s) => s.setContestType);

  // Decode the stored value back to primary/sub-type split
  const isPrimaryCandidate = contestType === 'candidate';
  const isPrimaryMeasure = contestType === 'measure';
  const isSubType = contestType !== null && contestType !== 'candidate' && contestType !== 'measure';
  const activePrimary = isPrimaryMeasure ? 'measure' : isPrimaryCandidate || isSubType ? 'candidate' : null;
  const activeSubType = isSubType ? contestType : null;

  const handlePrimary = (value: string | null) => {
    if (value === activePrimary && !isSubType) {
      // Re-clicking the active primary chip resets to "All"
      setContestType(null);
    } else {
      setContestType(value);
    }
  };

  const handleSubType = (value: string) => {
    if (activeSubType === value) {
      // Re-clicking active sub-type resets to "Elections" (candidate)
      setContestType('candidate');
    } else {
      setContestType(value);
    }
  };

  return (
    <Stack spacing={1}>
      <Stack aria-label="Filter by contest type" direction="row" flexWrap="wrap" gap={1} role="group">
        {PRIMARY_OPTIONS.map((opt) => {
          const isActive = opt.value === activePrimary && !isSubType;
          return (
            <Chip
              key={opt.label}
              color={isActive ? 'primary' : 'default'}
              label={opt.label}
              onClick={() => handlePrimary(opt.value)}
              size="small"
              variant={isActive ? 'filled' : 'outlined'}
            />
          );
        })}
      </Stack>

      {(isPrimaryCandidate || isSubType) && (
        <Stack
          aria-label="Filter by election type"
          direction="row"
          flexWrap="wrap"
          gap={1}
          role="group"
          sx={{ pl: 0.5 }}
        >
          <Typography color="text.secondary" sx={{ alignSelf: 'center' }} variant="caption">
            Type:
          </Typography>
          {ELECTION_SUB_TYPES.map((sub) => {
            const isActive = activeSubType === sub.value;
            return (
              <Chip
                key={sub.value}
                color={isActive ? 'secondary' : 'default'}
                label={sub.label}
                onClick={() => handleSubType(sub.value)}
                size="small"
                variant={isActive ? 'filled' : 'outlined'}
              />
            );
          })}
        </Stack>
      )}
    </Stack>
  );
}

export default ContestTypeFilter;
