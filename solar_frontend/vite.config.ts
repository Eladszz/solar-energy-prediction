import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import {defineConfig, loadEnv} from 'vite';

export default defineConfig(({mode}) => {
  const env = loadEnv(mode, '.', '');
  const backendTarget = env.VITE_API_PROXY_TARGET || env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      // Do not modifyâfile watching is disabled to prevent flickering during agent edits.
      hmr: process.env.DISABLE_HMR !== 'true',
      fs: {
        allow: [path.resolve(__dirname), path.resolve(__dirname, '..')],
      },
      proxy: {
        '/api': backendTarget,
        '/health': backendTarget,
        '/simulate': backendTarget,
        '/forecast': backendTarget,
        '/scenarios': backendTarget,
        '/swagger': backendTarget,
        '/redoc': backendTarget,
        '/openapi.json': backendTarget,
      },
    },
  };
});
