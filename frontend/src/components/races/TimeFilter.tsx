import { Chip, Stack, Typography } from '@mui/material';
import { useRaceFiltersStore } from '../../store/raceFiltersStore';
import { type TimeFilter, timeFilterLabel } from '../../utils/timeFilter';

const TIME_OPTIONS: TimeFilter[] = ['month', 'year', 'historical'];

function TimeFilterComponent() {
  const timeFilter = useRaceFiltersStore((s) => s.timeFilter);
  const setTimeFilter = useRaceFiltersStore((s) => s.setTimeFilter);

  return (
    <Stack aria-label="Filter by time period" direction="row" flexWrap="wrap" gap={1} role="group" alignItems="center">
      <Typography color="text.secondary" sx={{ alignSelf: 'center' }} variant="caption">
        When:
      </Typography>
      {TIME_OPTIONS.map((value) => {
        const isActive = timeFilter === value;
        return (
          <Chip
            key={value}
            color={isActive ? 'info' : 'default'}
            label={timeFilterLabel(value)}
            onClick={() => { setTimeFilter(value); }}
            size="small"
            variant={isActive ? 'filled' : 'outlined'}
          />
        );
      })}
    </Stack>
  );
}

export default TimeFilterComponent;
