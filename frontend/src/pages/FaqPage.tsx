import { Box, Card, CardContent, Stack, Typography } from '@mui/material';

interface FaqItem {
  question: string;
  answer: string;
  /** Optional bullet points rendered below `answer`, for lists-within-an-answer. */
  bullets?: Array<{ label: string; text: string }>;
}

const FAQ_ITEMS: FaqItem[] = [
  {
    question: 'What is CivicMirror?',
    answer:
      'CivicMirror is an open civic engagement platform that imports real U.S. election data and allows anyone to cast a mock vote, regardless of age, citizenship, or country of residence. After official results are certified, the platform compares mock vote outcomes against real-world results.',
  },
  {
    question: 'Is CivicMirror an official voting platform?',
    answer:
      'No. CivicMirror is not an official election authority and is not affiliated with any government agency or political organization. Mock votes on CivicMirror have no legal effect.',
  },
  {
    question: 'Who can participate in CivicMirror mock votes?',
    answer:
      'Anyone worldwide can browse races and cast mock votes on CivicMirror. There are no eligibility restrictions based on age, citizenship, or location.',
  },
  {
    question: 'Where does CivicMirror get its election data?',
    answer:
      'CivicMirror imports real election data from the Google Civic Information API, OpenFEC, Open States, OpenElections, and direct integrations with state Secretary of State offices. All 50 states are covered.',
  },
  {
    question: 'What do the labels on a race page mean?',
    answer:
      "Every race page shows a few small colored labels (we call them \"pills\") next to the race title. Here's what each one is telling you:",
    bullets: [
      {
        label: 'Civic API / Community',
        text: 'Where the race information came from. "Civic API" means it was imported automatically from an official government data source. "Community" means a CivicMirror user submitted it by hand.',
      },
      {
        label: 'General, Primary, Special Election, etc.',
        text: 'What stage of the election this is. A "Primary" narrows down each party’s candidates; the "General" election is the final vote for the seat. You may also see "Runoff," "Special Election," or "Municipal" for less common cases.',
      },
      {
        label: 'Active, Pending Review, Cancelled, Archived',
        text: '"Active" means the race is open for mock voting right now. "Pending Review" or "Draft" means it’s not open yet. "Cancelled" means the race was called off, and "Archived" means it’s over and closed to new votes.',
      },
      {
        label: 'Upcoming, Results Pending, Unofficial, Partial Results, Certified Results',
        text: 'How far along the real-world results are. "Upcoming" means the election hasn’t happened yet. "Unofficial" and "Partial Results" mean early or incomplete counts are in. "Certified Results" means the official, final count has been confirmed by election authorities.',
      },
    ],
  },
];

function buildFaqPageSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: FAQ_ITEMS.map((item) => ({
      '@type': 'Question',
      name: item.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: item.bullets
          ? `${item.answer} ${item.bullets.map((b) => `${b.label}: ${b.text}`).join(' ')}`
          : item.answer,
      },
    })),
  };
}

function FaqPage() {
  return (
    <Stack spacing={4}>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(buildFaqPageSchema()) }}
      />
      <Card>
        <CardContent sx={{ p: { xs: 3, md: 5 } }}>
          <Stack spacing={3}>
            <Box>
              <Typography gutterBottom variant="h1" sx={{ fontSize: 'clamp(1.5rem, 3.5vw, 2.25rem)' }}>
                Frequently Asked Questions
              </Typography>
              <Typography color="text.secondary" maxWidth={760} variant="h6">
                Answers to the most common questions about what CivicMirror is, how it works, and where
                its election data comes from.
              </Typography>
            </Box>
            <Stack spacing={3} component="section" aria-label="Frequently asked questions">
              {FAQ_ITEMS.map((item) => (
                <Stack key={item.question} spacing={0.5}>
                  <Typography variant="subtitle1" fontWeight={700} component="h2">
                    {item.question}
                  </Typography>
                  <Typography color="text.secondary" variant="body2">
                    {item.answer}
                  </Typography>
                  {item.bullets ? (
                    <Stack component="ul" spacing={1} sx={{ m: 0, mt: 1, pl: 3 }}>
                      {item.bullets.map((bullet) => (
                        <Typography key={bullet.label} color="text.secondary" component="li" variant="body2">
                          <Typography color="text.primary" component="span" fontWeight={600}>
                            {bullet.label}:
                          </Typography>{' '}
                          {bullet.text}
                        </Typography>
                      ))}
                    </Stack>
                  ) : null}
                </Stack>
              ))}
            </Stack>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}

export default FaqPage;
