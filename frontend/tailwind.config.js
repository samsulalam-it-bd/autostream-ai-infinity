/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                brand: {
                    50: '#f0f4ff',
                    100: '#e0e9ff',
                    200: '#c7d7fe',
                    300: '#a5b8fc',
                    400: '#8193f8',
                    500: '#6470f3',
                    600: '#4f52e8',
                    700: '#4140cd',
                    800: '#3637a6',
                    900: '#313284',
                    950: '#1e1d4d',
                },
                surface: {
                    50: '#f8f9ff',
                    100: '#f0f1f9',
                    200: '#e2e3f0',
                    300: '#cbcce0',
                    400: '#a8aaca',
                    500: '#8688b3',
                    600: '#6a6c97',
                    700: '#575979',
                    800: '#494b64',
                    900: '#3f4054',
                    950: '#15151f',
                },
                dark: {
                    100: '#1a1b25',
                    200: '#13141c',
                    300: '#0e0f16',
                    400: '#090a0f',
                },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
            },
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
                'hero-glow': 'radial-gradient(ellipse at 50% 0%, rgba(100, 112, 243, 0.15) 0%, transparent 60%)',
            },
            animation: {
                'pulse-slow': 'pulse 3s ease-in-out infinite',
                'blink': 'blink 1s step-end infinite',
                'slide-in': 'slideIn 0.3s ease-out',
                'fade-in': 'fadeIn 0.4s ease-out',
            },
            keyframes: {
                blink: { '0%, 100%': { opacity: 1 }, '50%': { opacity: 0 } },
                slideIn: { from: { transform: 'translateX(-10px)', opacity: 0 }, to: { transform: 'translateX(0)', opacity: 1 } },
                fadeIn: { from: { opacity: 0, transform: 'translateY(8px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
            },
            boxShadow: {
                'glow-brand': '0 0 30px rgba(100, 112, 243, 0.25)',
                'glow-green': '0 0 20px rgba(34, 197, 94, 0.2)',
                'glow-red': '0 0 20px rgba(239, 68, 68, 0.2)',
                'card': '0 4px 24px rgba(0, 0, 0, 0.3)',
            },
        },
    },
    plugins: [],
}
