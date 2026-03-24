import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        studio: {
          950: '#06070A',
          900: '#0B0D12',
          850: '#0F1118',
          800: '#131722',
          750: '#171C28',
          700: '#1C2433',
          650: '#243045',
          600: '#2D3D59',
          500: '#5B79B6',
          400: '#8EA5D8',
          300: '#B8C6E5'
        },
        accent: {
          blue: '#5B8CFF',
          cyan: '#5EEAD4',
          violet: '#8B5CF6',
          green: '#34D399',
          amber: '#FBBF24'
        }
      },
      boxShadow: {
        chrome: '0 24px 80px rgba(0,0,0,0.45)',
        panel: '0 10px 30px rgba(0,0,0,0.28)',
        glow: '0 0 0 1px rgba(91,140,255,0.18), 0 8px 40px rgba(91,140,255,0.12)',
      },
      backgroundImage: {
        grid: 'linear-gradient(rgba(148,163,184,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.06) 1px, transparent 1px)',
        noise: 'radial-gradient(circle at top, rgba(91,140,255,0.18), transparent 32%), radial-gradient(circle at bottom right, rgba(94,234,212,0.08), transparent 24%)',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      fontFamily: {
        sans: ['var(--font-inter)'],
        mono: ['var(--font-mono)'],
      },
    },
  },
  plugins: [],
}

export default config
