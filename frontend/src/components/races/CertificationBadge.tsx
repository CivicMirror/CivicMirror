import { Chip } from '@mui/material';
import type { Race } from '../../types';
import { RESULT_STATUS_MAP } from '../../utils/resultStatus';

interface CertificationBadgeProps {
  status: Race['certification_status'];
}

function CertificationBadge({ status }: CertificationBadgeProps) {
  const config = RESULT_STATUS_MAP[status];

  return <Chip color={config.color} label={config.label} size="small" variant={config.variant} />;
}

export default CertificationBadge;
