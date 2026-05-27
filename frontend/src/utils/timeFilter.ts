export type TimeFilter = 'month' | 'year' | 'historical';

export interface TimeBounds {
  election_date__gte?: string;
  election_date__lte?: string;
  race_status?: string;
}

function pad(n: number): string {
  return String(n).padStart(2, '0');
}

export function getTimeBounds(filter: TimeFilter): TimeBounds {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth(); // 0-indexed
  const lastDay = new Date(year, month + 1, 0).getDate();

  switch (filter) {
    case 'month':
      return {
        election_date__gte: `${year}-${pad(month + 1)}-01`,
        election_date__lte: `${year}-${pad(month + 1)}-${pad(lastDay)}`,
        race_status: 'active',
      };
    case 'year':
      return {
        election_date__gte: `${year}-01-01`,
        election_date__lte: `${year}-12-31`,
        race_status: 'active',
      };
    case 'historical':
      return {
        election_date__lte: `${year - 1}-12-31`,
        race_status: 'archived',
      };
  }
}

const MONTH_NAMES = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
] as const;

export function timeFilterLabel(filter: TimeFilter): string {
  const now = new Date();
  switch (filter) {
    case 'month':
      return `${MONTH_NAMES[now.getMonth()]} ${now.getFullYear()}`;
    case 'year':
      return String(now.getFullYear());
    case 'historical':
      return 'Historical';
  }
}
