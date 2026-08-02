import Chip from '@mui/material/Chip';

interface PartyPillProps {
  normalized_party: string | null | undefined;
  election_type: string;
}

// Contrast-checked against white: REP red ~4.55:1, DEM blue ~7.9:1,
// CON navy ~16:1, WFP orange ~4.9:1 (WCAG AA requires >=4.5:1).
// Map lookup with a gray fallback so a third-party color is a one-line addition later.
const PARTY_COLORS: Record<string, string> = {
  DEM: '#0044c9',
  REP: '#e81b23',
  // NY Conservative Party (cpnys.org) official navy blue.
  CON: '#002244',
  // Working Families Party's brand "Working Orange" (#F4563B) is only
  // ~3.36:1 against white -- fails WCAG AA for this chip's small text.
  // Darkened along the same hue/saturation to ~4.9:1 rather than switching
  // to an unrelated color. See issue #124 / CivicMirror-API#124.
  WFP: '#D92A0C',
};

const FALLBACK_COLOR = '#616161';

// Only these election types render one race per party for the same seat/date;
// a general-election race with one candidate per party is not "the Democratic race."
const PRIMARY_ELECTION_TYPES = new Set(['primary', 'primary_runoff', 'party']);

// Keeps unknown/third-party codes from normalize_party (which can be an arbitrarily
// long uppercased string) from blowing up the chip past the size of "Primary Runoff".
const MAX_LABEL_LENGTH = 14;

function PartyPill({ normalized_party, election_type }: PartyPillProps) {
  if (!normalized_party) return null;
  if (normalized_party === 'NP') return null;
  if (!PRIMARY_ELECTION_TYPES.has(election_type.toLowerCase())) return null;

  const code = normalized_party.toUpperCase();
  const color = PARTY_COLORS[code] ?? FALLBACK_COLOR;
  const label = code.length > MAX_LABEL_LENGTH ? `${code.slice(0, MAX_LABEL_LENGTH - 1)}…` : code;

  return (
    <Chip
      label={label}
      size="small"
      sx={{ color, borderColor: color }}
      variant="outlined"
    />
  );
}

export default PartyPill;
