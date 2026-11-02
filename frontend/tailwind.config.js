/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paytm: {
          blue: "#00BAF2",
          cyan: "#00BAF2",
          darkNavy: "#002970",
          lightBlue: "#EBF8FD",
          deepBlue: "#001B48",
          accentCyan: "#00E5FF",
        }
      },
      screens: {
        xs: "420px",
      }
    },
  },
  plugins: [],
}
