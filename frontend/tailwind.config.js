/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#8B5CF6',
        secondary: '#F59E0B',
        dark: {
          900: '#0a0a0a',
          850: '#0f0f0f',
          800: '#121212',
          700: '#1a1a1a',
          600: '#252525',
          500: '#333333',
        }
      },
    },
  },
  plugins: [],
}
