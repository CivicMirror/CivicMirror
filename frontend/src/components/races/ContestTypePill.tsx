import Chip from '@mui/material/Chip';

interface ContestTypePillProps {
  ballot_type: string;
}

type ChipColor = 'default' | 'primary' | 'secondary' | 'info' | 'success' | 'warning' | 'error';

const KNOWN_TYPES: Record<string, { label: string; color: ChipColor }> = {
  general: { label: 'General Election', color: 'primary' },
  primary: { label: 'Primary', color: 'info' },
  'run-off': { label: 'Run-off', color: 'warning' },
  referendum: { label: 'Ballot Measure', color: 'success' },
  // Civic API returns 'ballot-measure' in practice (undocumented kebab form)
  'ballot-measure': { label: 'Ballot Measure', color: 'success' },
  retention: { label: 'Retention Vote', color: 'secondary' },
};

function ContestTypePill({ ballot_type }: ContestTypePillProps) {
  if (!ballot_type) return null;

  const match = KNOWN_TYPES[ballot_type.toLowerCase()];

  if (match) {
    return <Chip color={match.color} label={match.label} size="small" />;
  }

  // Unknown future type — display title-cased, neutral chip
  const label = ballot_type.charAt(0).toUpperCase() + ballot_type.slice(1).toLowerCase();
  return <Chip label={label} size="small" />;
}

export default ContestTypePill;
