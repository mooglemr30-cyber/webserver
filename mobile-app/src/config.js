// Server Configuration
// Update this with your server's tunnel URL

const CONFIG = {
  // Server URL - will be fetched from server or set manually
  SERVER_URL: null, // Will be auto-configured

  // Local server URL (when on same network)
  LOCAL_SERVER_URL: 'http://localhost:8000',

  // API endpoints
  API: {
    HEALTH: '/health',
    MOBILE_CONFIG: '/api/mobile/config',
    TUNNEL_STATUS: '/api/mobile/tunnel/status',
    TUNNEL_START: '/api/mobile/tunnel/start',
    TUNNEL_STOP: '/api/mobile/tunnel/stop',
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    DATA: '/api/data',
    FILES: '/api/files',
    PROGRAMS: '/api/programs',
    EXECUTE: '/api/execute',
  },

  // Timeout settings (ms)
  TIMEOUT: {
    DEFAULT: 10000,
    UPLOAD: 60000,
    DOWNLOAD: 60000,
    EXECUTE: 120000,
  },

  // Storage keys
  STORAGE_KEYS: {
    SERVER_URL: '@webserver:server_url',
    AUTH_TOKEN: '@webserver:auth_token',
    USER_INFO: '@webserver:user_info',
    USE_TUNNEL: '@webserver:use_tunnel',
  },

  // Default to local connection
  DEFAULT_SERVER_URL: 'http://localhost:8000',
};

export default CONFIG;

