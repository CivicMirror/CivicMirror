import type { ChipProps } from '@mui/material';
import { Chip } from '@mui/material';
import type { Race } from '../../types';

type RaceStatusKey = Race['race_status'];

const STATUS_MAP: Record<RaceStatusKey, { label: string; color: ChipProps['color'] }> = {
  draft: { label: 'Draft', color: 'default' },
  pending_review: { label: 'Pending Review', color: 'warning' },
  active: { label: 'Active', color: 'success' },
  cancelled: { label: 'Cancelled', color: 'error' },
  archived: { label: 'Archived', color: 'default' },
};

function StatusChip({ race_status }: Pick<Race, 'race_status'>) {
  const config = STATUS_MAP[race_status];

  return <Chip color={config.color} label={config.label} size="small" />;
}

export { STATUS_MAP };
export default StatusChip;
