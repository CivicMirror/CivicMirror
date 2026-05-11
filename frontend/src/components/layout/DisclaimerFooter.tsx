import InfoOutlined from '@mui/icons-material/InfoOutlined';
import { Box, Container, Typography } from '@mui/material';

function DisclaimerFooter() {
  return (
    <Box
      bgcolor="common.white"
      borderTop={(theme) => `1px solid ${theme.palette.divider}`}
      component="footer"
      mt={6}
      py={2.5}
    >
      <Container maxWidth="lg">
        <Box alignItems="flex-start" display="flex" gap={1.5}>
          <InfoOutlined color="primary" fontSize="small" sx={{ mt: 0.2 }} />
          <Typography color="text.secondary" variant="body2">
            CivicMirror mock votes are for informational and community engagement purposes only.
            They have no legal effect, are not affiliated with any official election authority, and
            do not represent official results.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default DisclaimerFooter;
