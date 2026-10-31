/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: '/paypoint',
  // Vercel supplies its own serverless output adapter.
  ...(process.env.VERCEL === '1' ? {} : {output: 'standalone'}),
  skipTrailingSlashRedirect: true,
  poweredByHeader: false,
  // The application is staff-only; API and session responses must never be shared.
  async headers() {
    return [{source:'/:path*',headers:[
      {key:'X-Content-Type-Options',value:'nosniff'},
      {key:'Referrer-Policy',value:'same-origin'},
      {key:'X-Frame-Options',value:'DENY'},
      {key:'X-Robots-Tag',value:'noindex, nofollow'},
      {key:'Permissions-Policy',value:'camera=(), microphone=(), geolocation=()'},
    ]}];
  },
};
export default nextConfig;
