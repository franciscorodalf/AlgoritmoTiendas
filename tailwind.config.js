/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        ink: "#111317",
        muted: "#64707d",
        brand: {
          50: "#eff8f5",
          100: "#d9eee8",
          500: "#23635a",
          700: "#154b45",
          900: "#0b2927",
        },
        copper: "#c8843b",
      },
      boxShadow: {
        premium: "0 24px 80px rgba(17, 19, 23, 0.14)",
        soft: "0 16px 48px rgba(17, 19, 23, 0.09)",
      },
      transitionTimingFunction: {
        smooth: "cubic-bezier(.16,1,.3,1)",
      },
    },
  },
  plugins: [],
};
