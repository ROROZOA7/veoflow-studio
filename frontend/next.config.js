/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['localhost'],
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  // Use polling instead of inotify to avoid file watcher limit issues
  webpack: (config, { dev, isServer }) => {
    if (dev) {
      // Enable polling to bypass inotify file watcher limit
      config.watchOptions = {
        poll: 1000, // Check for changes every second (use polling)
        aggregateTimeout: 300, // Wait 300ms before triggering rebuild
        ignored: [
          '**/node_modules/**',
          '**/.next/**',
          '**/dist/**',
          '**/build/**',
          '**/.git/**',
          '**/coverage/**',
          '**/tmp/**',
          '**/temp/**',
          '**/.cache/**',
          '**/.turbo/**',
          '**/backend/**',
          '**/profiles/**',
          '**/output/**',
          '**/logs/**',
          '**/images/**',
        ],
      }
    }
    return config
  },
}

module.exports = nextConfig

