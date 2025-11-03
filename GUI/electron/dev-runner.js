const { spawn } = require('child_process');
const { app } = require('electron');

// Set development environment
process.env.NODE_ENV = 'development';

// Wait for Vite dev server to be ready
const waitForServer = () => {
  return new Promise((resolve) => {
    const checkServer = () => {
      const http = require('http');
      const req = http.request('http://localhost:5173', (res) => {
        resolve();
      });
      req.on('error', () => {
        setTimeout(checkServer, 1000);
      });
      req.end();
    };
    checkServer();
  });
};

// Start the main process
const startElectron = async () => {
  await waitForServer();
  require('./main.cjs');
};

if (require.main === module) {
  startElectron();
}
