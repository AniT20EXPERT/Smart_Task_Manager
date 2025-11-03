import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: './', // Needed for Electron so assets resolve correctly
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      // Don't force manualChunks: undefined unless you need a single bundle
      // It's safer to omit this unless you have a reason
    }
  },
  resolve: {
    dedupe: ['react', 'react-dom'],
    // Avoid aliasing Node built-ins in the renderer; use preload + IPC for Node access
  },
  optimizeDeps: {
    include: ['lucide-react']
  },
  server: {
    port: 5173,
    strictPort: true
  }
});
