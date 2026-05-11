import { Box, Container } from '@mui/material';
import { Outlet } from 'react-router-dom';
import DisclaimerFooter from './DisclaimerFooter';
import Header from './Header';

function AppLayout() {
  return (
    <Box display="flex" flexDirection="column" minHeight="100vh">
      <Header />
      <Box component="main" flex={1} py={{ xs: 3, md: 5 }}>
        <Container maxWidth="lg">
          <Outlet />
        </Container>
      </Box>
      <DisclaimerFooter />
    </Box>
  );
}

export default AppLayout;
