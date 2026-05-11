import { Box, LinearProgress, Stack, Typography } from '@mui/material';
import type { TallyOption } from '../../types';
import { formatPercent } from '../../utils/format';

interface TallyBarsProps {
  options: TallyOption[];
  totalVotes: number;
  compact?: boolean;
  showTotal?: boolean;
}

function TallyBars({ options, totalVotes, compact = false, showTotal = true }: TallyBarsProps) {
  if (!options.length) {
    return (
      <Typography color="text.secondary" variant="body2">
        Mock tally data will appear here once people begin casting votes.
      </Typography>
    );
  }

  return (
    <Stack spacing={compact ? 1 : 1.5}>
      {options.map((option, index) => {
        const isLeading = index === 0;
        return (
          <Stack key={`${option.type}-${option.id}`} spacing={0.75}>
            <Stack alignItems="center" direction="row" justifyContent="space-between" spacing={1}>
              <Typography fontWeight={isLeading ? 700 : 500} variant={compact ? 'body2' : 'body1'}>
                {option.label}
              </Typography>
              <Typography color="text.secondary" variant={compact ? 'caption' : 'body2'}>
                {option.count} · {formatPercent(option.percent)}
              </Typography>
            </Stack>
            <Box>
              <LinearProgress
                color={isLeading ? 'primary' : 'secondary'}
                sx={{
                  borderRadius: 999,
                  height: compact ? 8 : 10,
                  opacity: isLeading ? 1 : 0.82,
                }}
                value={option.percent}
                variant="determinate"
              />
            </Box>
          </Stack>
        );
      })}
      {showTotal ? (
        <Typography color="text.secondary" variant={compact ? 'caption' : 'body2'}>
          {totalVotes} mock votes cast
        </Typography>
      ) : null}
    </Stack>
  );
}

export default TallyBars;
