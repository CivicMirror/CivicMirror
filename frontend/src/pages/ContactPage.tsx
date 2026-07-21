import Email from '@mui/icons-material/Email';
import Facebook from '@mui/icons-material/Facebook';
import Forum from '@mui/icons-material/Forum';
import VolunteerActivism from '@mui/icons-material/VolunteerActivism';
import { Box, Card, CardContent, Divider, Link, Stack, Typography } from '@mui/material';

const CONTACT_EMAIL = 'support@civicmirror.app';

const SOCIAL_LINKS = [
  {
    label: 'Facebook Group',
    href: 'https://www.facebook.com/groups/1788521338910165',
    icon: <Facebook color="primary" fontSize="small" />,
  },
  {
    label: 'Chat with us on Unified.me',
    href: 'https://unified.me/chat/!LyjuOFfDzaihbrkNkE',
    icon: <Forum color="primary" fontSize="small" />,
  },
  {
    label: 'CivicMirror on DemocracyLab',
    href: 'https://www.democracylab.org/projects/2005',
    icon: <VolunteerActivism color="primary" fontSize="small" />,
  },
];

function ContactPage() {
  return (
    <Box display="flex" justifyContent="center" py={{ xs: 2, md: 6 }}>
      <Card sx={{ maxWidth: 640, width: '100%' }}>
        <CardContent sx={{ p: { xs: 3, md: 4 } }}>
          <Stack spacing={2}>
            <Typography gutterBottom variant="h1" sx={{ fontSize: 'clamp(1.5rem, 3.5vw, 2.25rem)' }}>
              Contact Us
            </Typography>
            <Typography color="text.secondary">
              For state data issues, technical issues, support assistance, or general questions,
              please contact us at:
            </Typography>
            <Stack alignItems="center" direction="row" spacing={1}>
              <Email color="primary" fontSize="small" />
              <Link href={`mailto:${CONTACT_EMAIL}`} variant="h6">
                {CONTACT_EMAIL}
              </Link>
            </Stack>

            <Divider sx={{ my: 1 }} />

            <Box>
              <Typography gutterBottom variant="subtitle1" fontWeight={700}>
                Find us elsewhere
              </Typography>
              <Stack spacing={1.5}>
                {SOCIAL_LINKS.map((social) => (
                  <Stack key={social.href} alignItems="center" direction="row" spacing={1}>
                    {social.icon}
                    <Link href={social.href} rel="noopener noreferrer" target="_blank" variant="body1">
                      {social.label}
                    </Link>
                  </Stack>
                ))}
              </Stack>
            </Box>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}

export default ContactPage;
