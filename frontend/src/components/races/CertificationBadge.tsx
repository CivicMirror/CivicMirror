import type { ChipProps } from '@mui/material';
import { Chip } from '@mui/material';
import type { Race } from '../../types';

interface CertificationBadgeProps {
  status: Race['certification_status'];
}

const CERTIFICATION_MAP: Record<
  Race['certification_status'],
  { label: string; color: ChipProps['color']; variant: ChipProps['variant'] }
> = {
  upcoming: { label: 'Upcoming', color: 'default', variant: 'outlined' },
  results_pending: { label: 'Results Pending', color: 'warning', variant: 'outlined' },
  results_certified: { label: 'Official Results', color: 'success', variant: 'filled' },
  partial_results: { label: 'Partial Results', color: 'warning', variant: 'filled' },
};

function CertificationBadge({ status }: CertificationBadgeProps) {
  const config = CERTIFICATION_MAP[status];

  return <Chip color={config.color} label={config.label} size="small" variant={config.variant} />;
}

export default CertificationBadge;
