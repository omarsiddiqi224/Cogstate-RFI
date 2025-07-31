/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#231F20',
        'secondary': '#0097AC',
        'header-icon': '#8c9bae',
        'light-gray': '#f2f7fd'
      },
    },
  },
  plugins: [],
}