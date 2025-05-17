// Cloudflare Pages build configuration
export default {
  build: {
    command: 'cd frontend && npm install && npm run build',
    directory: 'frontend/dist',
    publicPath: '/'
  },
  routes: [
    { pattern: '/assets/*', path: '/assets/:splat' },
    { pattern: '/*', path: '/index.html', headers: { 'Cache-Control': 'no-cache' } }
  ]
}
