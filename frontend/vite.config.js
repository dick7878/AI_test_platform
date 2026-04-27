import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

function mockApiPlugin() {
  return {
    name: 'mock-api-plugin',
    configureServer(server) {
      server.middlewares.use('/api/test', (_req, res) => {
        res.setHeader('Content-Type', 'application/json; charset=utf-8')
        res.end(
          JSON.stringify({
            code: 0,
            message: 'ok',
            data: {
              source: 'vite-mock',
              timestamp: new Date().toISOString(),
            },
          }),
        )
      })
    },
  }
}

export default defineConfig({
  plugins: [vue(), mockApiPlugin()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
