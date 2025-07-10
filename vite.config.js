import { defineConfig } from 'vite'

export default defineConfig({
  root: 'static',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: 'static/main.js'
      }
    }
  },
  server: {
    port: 3000,
    cors: true,
    // Allow HMR to work with Flask templates
    hmr: {
      port: 3001
    },
    // Don't proxy everything - let Flask handle templates
    proxy: {
      // Only proxy API calls to Flask
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})