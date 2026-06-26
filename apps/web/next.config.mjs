/** @type {import("next").NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@urim/config", "@urim/ui", "@urim/contracts"]
};

export default nextConfig;
