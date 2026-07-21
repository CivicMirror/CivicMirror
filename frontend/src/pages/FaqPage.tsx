import { Box, Card, CardContent, Stack, Typography } from '@mui/material';

const FAQ_ITEMS: Array<{ question: string; answer: string }> = [
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
        text: item.answer,
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
