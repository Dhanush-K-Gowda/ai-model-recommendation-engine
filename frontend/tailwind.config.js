/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0a0a', // Almost black
        surface: '#1a1a1a', // Dark grey
        'surface-hover': '#252525',
        primary: '#9ca3af', // Medium grey
        'primary-glow': '#d1d5db', // Light grey
        secondary: '#6b7280', // Darker grey
        accent: '#71717a', // Neutral grey
        border: 'rgba(255, 255, 255, 0.08)',
        text: {
          main: '#f3f4f6', // Cool white
          muted: '#9ca3af', // Grey
        }
      },
      fontFamily: {
        sans: ['Outfit', 'sans-serif'], // Modern, geometric
        mono: ['JetBrains Mono', 'monospace'], // For code/numbers
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.5s ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [],
}
