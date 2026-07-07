/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  typedRoutes: false,
  images: {
    domains: ['api.dicebear.com', 'avatars.githubusercontent.com'],
  },
};

module.exports = nextConfig;
