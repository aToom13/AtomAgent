/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#f0f9ff',
          500: '#00D4FF',
          600: '#0EA5E9',
          700: '#0284C7',
        },
        secondary: {
          500: '#A855F7',
          600: '#9333EA',
        },
      },
      animation: {
        'gradient-shift': 'gradient-shift 8s ease infinite',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'typing': 'typing 1.4s infinite',
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'glow-sm': '0 0 10px rgba(14, 165, 233, 0.3)',
        'glow-md': '0 0 20px rgba(14, 165, 233, 0.4)',
        'glow-lg': '0 0 30px rgba(14, 165, 233, 0.5)',
      },
    },
  },
  plugins: [],
};