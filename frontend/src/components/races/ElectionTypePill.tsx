import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';

interface ElectionTypePillProps {
  election_type: string;
}

const KNOWN_TYPES: Record<string, { label: string; color: ChipProps['color'] }> = {
  general: { label: 'General', color: 'default' },
  primary: { label: 'Primary', color: 'info' },
  primary_runoff: { label: 'Primary Runoff', color: 'warning' },
  special: { label: 'Special Election', color: 'secondary' },
  general_runoff: { label: 'General Runoff', color: 'warning' },
  municipal: { label: 'Municipal', color: 'default' },
  party: { label: 'Party', color: 'default' },
  other: { label: 'Other', color: 'default' },
};

// Always renders, including "General" — two races for the same seat/date
// range (e.g. a primary and its general) must read as distinct at a glance
// even in isolation, so the label can't be conveyed by absence.
function ElectionTypePill({ election_type }: ElectionTypePillProps) {
  if (!election_type) return null;

  const match = KNOWN_TYPES[election_type.toLowerCase()];

  if (match) {
    return <Chip color={match.color} label={match.label} size="small" variant="outlined" />;
  }

  const label = election_type.charAt(0).toUpperCase() + election_type.slice(1).toLowerCase();
  return <Chip label={label} size="small" variant="outlined" />;
}

export default ElectionTypePill;
