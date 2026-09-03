/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#0a0d12",
        panel: "#12161f",
        "panel-alt": "#171c27",
        border: "#232838",
        amber: {
          DEFAULT: "#ffb627",
          dim: "#8a6a2a",
        },
        cyan: {
          DEFAULT: "#4ce0c6",
          dim: "#2f6b60",
        },
        text: "#eceff3",
        muted: "#8891a3",
      },
      fontFamily: {
        mono: ["IBM Plex Mono", "monospace"],
        sans: ["IBM Plex Sans", "sans-serif"],
        display: ["Space Grotesk", "sans-serif"],
      },
    },
  },
  plugins: [],
};
