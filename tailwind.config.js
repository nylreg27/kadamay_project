// E:\my_project\kadamay_project\tailwind.config.js

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html', // For templates directly in the project root (if any)
    './theme/**/*.html', // This covers theme/templates and theme/static_src
    './apps/*/templates/**/*.html', // For templates inside your Django apps
    './apps/**/*.html', // Broader search for any other HTML files in apps
    './theme/static_src/src/**/*.{js,ts,jsx,tsx}', // If you have JS/TS files with Tailwind classes
  ],
  theme: {
    extend: {},
  },
  // KINI ANG IMONG KULANG, BRO! KINI ANG MAGPA-OUTPUT SA DAISYUI!
  plugins: [
    require('daisyui'),
  ],
  daisyui: {
    // These are the DaisyUI themes you want to include.
    // You can customize this list based on what you need.
    themes: [
      "light", "dark", "cupcake", "dracula", "emerald", "corporate", 
      "synthwave", "retro", "cyberpunk", "valentine", "halloween", 
      "garden", "forest", "aqua", "lofi", "pastel", "fantasy", 
      "wireframe", "black", "luxury", "dracula", "cmyk", "autumn", 
      "business", "acid", "lemonade", "night", "coffee", "winter", 
      "dim", "nord", "sunset"
    ],
    // Optional: Add other DaisyUI config if needed
    // darkTheme: "dark", // Specify which theme is dark
    // base: true, // Apply base styles
    // styled: true, // Apply component styles
    // utils: true, // Apply utility classes
    // rtl: false, // Right-to-left support
    // prefix: "", // Prefix for DaisyUI classes (e.g., "daisy-btn")
    // logs: true, // Show logs for theme generation
  },
};