import CheckCircle from '@mui/icons-material/CheckCircle';
import {
  Alert,
  Box,
  Link,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { getApiErrorMessage } from '../../api/client';
import { civicElectionsApi } from '../../api/civicElections';
import { getRaceOfficialResults } from '../../api/elections';
import { votingApi } from '../../api/voting';
import type { OfficialResultRow, OfficialResultsResponse, TallyResponse } from '../../types';
import type { CivicRaceDetail } from '../../types/civicApi';
import { formatPercent } from '../../utils/format';
import { civicResultsToLegacyResponse } from '../../utils/civicRaceAdapter';
import LoadingSpinner from '../common/LoadingSpinner';

interface OfficialResultsPanelProps {
  raceId: number;
  certificationStatus: string;
  /** Provide this when the race was fetched from the CivicMirror-API (new path).
   *  When present, official results and mock tally are fetched via the new API
   *  and external voting endpoints respectively. */
  civicRaceDetail?: CivicRaceDetail;
}

interface ComparisonRow {
  id: number;
  label: string;
  mockVotes: number | null;
  mockPct: number | null;
  officialVotes: number;
  officialPct: number | null;
  isWinner: boolean;
}

const numberFormatter = new Intl.NumberFormat('en-US');

const normalizePercent = (value?: number | null) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return null;
  }

  return value <= 1 ? value * 100 : value;
};

const formatVoteCount = (value?: number | null) => (value === null || value === undefined ? '—' : numberFormatter.format(value));

const formatVotePercent = (value?: number | null) => {
  const normalized = normalizePercent(value);
  return normalized === null ? '—' : formatPercent(normalized);
};

const getRowLabel = (row: OfficialResultRow) => {
  if (row.option_label) {
    return row.option_label;
  }

  if (row.candidate_name) {
    return row.candidate_name;
  }

  return row.is_write_in_aggregate ? 'Write-in (agg.)' : 'Unknown';
};

const normalizeLabel = (value: string) => {
  const normalized = value
    .trim()
    .toLowerCase()
    .replace(/\(.*?\)/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();

  if (['yes', 'for', 'approve', 'approved'].includes(normalized)) {
    return 'yes';
  }

  if (['no', 'against', 'reject', 'rejected'].includes(normalized)) {
    return 'no';
  }

  return normalized;
};

const getSourceDomain = (url: string) => {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return url;
  }
};

function OfficialResultsPanel({ raceId, certificationStatus, civicRaceDetail }: OfficialResultsPanelProps) {
  const [officialResults, setOfficialResults] = useState<OfficialResultsResponse | null>(null);
  const [mockTally, setMockTally] = useState<TallyResponse | null>(null);
  const [loading, setLoading] = useState(certificationStatus !== 'upcoming');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (certificationStatus === 'upcoming') {
      setOfficialResults(null);
      setMockTally(null);
      setLoading(false);
      setError(null);
      return;
    }

    let isActive = true;
    setLoading(true);
    setError(null);
    setOfficialResults(null);
    setMockTally(null);

    const officialResultsRequest = civicRaceDetail
      ? civicElectionsApi
          .getRaceResults(raceId)
          .then((results) => civicResultsToLegacyResponse(results, civicRaceDetail))
      : getRaceOfficialResults(raceId);

    const mockTallyRequest =
      certificationStatus === 'results_pending'
        ? Promise.resolve<TallyResponse | null>(null)
        : civicRaceDetail
          ? votingApi.getRaceTallyByExternalId(raceId)
          : votingApi.getRaceTally(raceId);

    void Promise.allSettled([officialResultsRequest, mockTallyRequest])
      .then(([officialResponse, mockTallyResponse]) => {
        if (!isActive) {
          return;
        }

        if (officialResponse.status === 'fulfilled') {
          setOfficialResults(officialResponse.value);
        } else if (certificationStatus !== 'results_pending') {
          setError(getApiErrorMessage(officialResponse.reason, 'We could not load official results right now.'));
        }

        if (mockTallyResponse.status === 'fulfilled') {
          setMockTally(mockTallyResponse.value);
        }
      })
      .finally(() => {
        if (isActive) {
          setLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [certificationStatus, civicRaceDetail, raceId]);

  const effectiveCertificationStatus = officialResults?.certification_status ?? certificationStatus;
  const rows = officialResults?.results ?? [];
  const hasUnofficialRows = rows.some((row) => row.result_type === 'unofficial');
  const sourceUrl = officialResults?.source_url || rows[0]?.source_url || '';

  const comparisonRows = useMemo<ComparisonRow[]>(() => {
    const mockOptions = new Map((mockTally?.options ?? []).map((option) => [normalizeLabel(option.label), option]));

    return rows.map((row) => {
      const label = getRowLabel(row);
      const mockMatch = row.is_write_in_aggregate ? undefined : mockOptions.get(normalizeLabel(label));

      return {
        id: row.id,
        label,
        mockVotes: row.is_write_in_aggregate ? null : mockMatch?.count ?? null,
        mockPct: row.is_write_in_aggregate ? null : normalizePercent(mockMatch?.percent),
        officialVotes: row.vote_count,
        officialPct: normalizePercent(row.vote_pct),
        isWinner: Boolean(row.is_winner),
      };
    });
  }, [mockTally?.options, rows]);

  if (certificationStatus === 'upcoming') {
    return null;
  }

  if (loading) {
    return <LoadingSpinner message="Loading official results…" minHeight={160} />;
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (effectiveCertificationStatus === 'results_pending') {
    return <Alert severity="info">Official results not yet available</Alert>;
  }

  if (comparisonRows.length === 0) {
    return null;
  }

  return (
    <Stack spacing={2}>
      {effectiveCertificationStatus === 'partial_results' ? (
        <Alert severity="warning">
          Official comparison is incomplete — some candidates could not be matched to the official feed.
        </Alert>
      ) : null}

      <Box sx={{ overflowX: 'auto' }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Candidate</TableCell>
              <TableCell align="right">Mock Votes</TableCell>
              <TableCell align="right">Mock %</TableCell>
              <TableCell align="right">Official Votes</TableCell>
              <TableCell align="right">Official %</TableCell>
              <TableCell align="center">Winner</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {comparisonRows.map((row) => (
              <TableRow key={row.id}>
                <TableCell component="th" scope="row">
                  {row.label}
                </TableCell>
                <TableCell align="right">{formatVoteCount(row.mockVotes)}</TableCell>
                <TableCell align="right">{formatVotePercent(row.mockPct)}</TableCell>
                <TableCell align="right">{formatVoteCount(row.officialVotes)}</TableCell>
                <TableCell align="right">{formatVotePercent(row.officialPct)}</TableCell>
                <TableCell align="center">
                  {row.isWinner ? <CheckCircle color="success" fontSize="small" titleAccess="Winner" /> : null}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Box>

      {hasUnofficialRows ? (
        <Typography color="warning.main" variant="caption">
          (unofficial)
        </Typography>
      ) : null}

      {sourceUrl ? (
        <Typography color="text.secondary" variant="caption">
          Source:{' '}
          <Link href={sourceUrl} rel="noreferrer" target="_blank" underline="hover">
            {getSourceDomain(sourceUrl)}
          </Link>
        </Typography>
      ) : null}
    </Stack>
  );
}

export default OfficialResultsPanel;
