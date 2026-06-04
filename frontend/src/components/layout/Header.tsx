import AccountCircle from '@mui/icons-material/AccountCircle';
import HowToVote from '@mui/icons-material/HowToVote';
import Login from '@mui/icons-material/Login';
import Logout from '@mui/icons-material/Logout';
import PersonAdd from '@mui/icons-material/PersonAdd';
import { AppBar, Box, Button, Stack, Toolbar, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

function Header() {
  const { displayName, isAuthenticated, isLoading, logout } = useAuth();

  return (
    <AppBar color="transparent" elevation={0} position="sticky" sx={{ backdropFilter: 'blur(14px)' }}>
      <Toolbar
        sx={{
          justifyContent: 'space-between',
          gap: 2,
          minHeight: { xs: 80, md: 88 },
          px: { xs: 2, md: 3 },
        }}
      >
        <Stack alignItems="center" component={RouterLink} direction="row" gap={1.5} to="/">
          <Box
            alignItems="center"
            bgcolor="primary.main"
            borderRadius="50%"
            color="common.white"
            display="inline-flex"
            height={42}
            justifyContent="center"
            width={42}
          >
            <HowToVote fontSize="small" />
          </Box>
          <Box>
            <Typography variant="h6">CivicMirror</Typography>
            <Typography color="text.secondary" variant="caption">
              Public mock voting for real elections
            </Typography>
          </Box>
        </Stack>

        <Stack direction="row" flexWrap="wrap" gap={1} justifyContent="flex-end">
          <Button component={RouterLink} to="/">
            Browse races
          </Button>
          <Button component={RouterLink} to="/coverage">
            Coverage
          </Button>

          {isAuthenticated ? (
            <>
              <Button component={RouterLink} startIcon={<AccountCircle />} to="/profile" variant="outlined">
                {displayName}
              </Button>
              <Button
                color="primary"
                disabled={isLoading}
                onClick={() => {
                  void logout();
                }}
                startIcon={<Logout />}
                variant="contained"
              >
                Log out
              </Button>
            </>
          ) : (
            <>
              <Button component={RouterLink} startIcon={<Login />} to="/login" variant="outlined">
                Log in
              </Button>
              <Button component={RouterLink} startIcon={<PersonAdd />} to="/register" variant="contained">
                Register
              </Button>
            </>
          )}
        </Stack>
      </Toolbar>
    </AppBar>
  );
}

export default Header;
