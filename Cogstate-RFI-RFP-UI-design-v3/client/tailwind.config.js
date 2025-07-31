/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#1a365d',
        'secondary': '#00a3e0',
        'header-icon': '#8c9bae',
        'light-gray': '#f2f7fd'
      },
    },
  },
  plugins: [],
}