/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef4fb",
          100: "#d9e6f5",
          500: "#2e75b6",
          600: "#255f93",
          700: "#1f3b57",
        },
      },
    },
  },
  plugins: [],
};
