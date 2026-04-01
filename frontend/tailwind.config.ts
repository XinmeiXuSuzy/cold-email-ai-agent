import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f7ff",
          100: "#e0efff",
          200: "#baddff",
          300: "#7cc2ff",
          400: "#36a4ff",
          500: "#0b85f0",
          600: "#0066cc",
          700: "#0052a3",
          800: "#004585",
          900: "#003a6e",
        },
      },
    },
  },
  plugins: [],
};
export default config;
