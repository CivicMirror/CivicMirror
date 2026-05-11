import type { ChipProps } from '@mui/material';
import { Chip } from '@mui/material';
import type { Race } from '../../types';
import { getRaceDisplayStatus, type DisplayStatusKey } from '../../utils/format';

const STATUS_MAP: Record<DisplayStatusKey, { label: string; color: ChipProps['color'] }> = {
  upcoming: { label: 'Upcoming', color: 'info' },
  active: { label: 'Active', color: 'success' },
  results_pending: { label: 'Results Pending', color: 'warning' },
  results_certified: { label: 'Certified', color: 'default' },
  archived: { label: 'Archived', color: 'default' },
};

function StatusChip(
  props: Pick<Race, 'certification_status' | 'race_status' | 'voting_opens' | 'voting_closes'>,
) {
  const status = getRaceDisplayStatus(props);
  const config = STATUS_MAP[status];

  return <Chip color={config.color} label={config.label} size="small" />;
}

export { STATUS_MAP };
export default StatusChip;
