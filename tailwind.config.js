/** @type {import('tailwindcss').Config} */
module.exports = {
    // Specify the files Tailwind should scan for utility classes.
    // This includes all HTML templates in the project and specific Django app templates.
    content: [
      './templates/**/*.html',     // Global templates folder (OKAY)
      './apps/**/*.html',         // All templates within Django apps (e.g., in apps/account/templates/account/*.html) (OKAY)
      './theme/**/*.html',        // General theme folder (includes direct HTML files)
      './theme/templates/**/*.html', // KINI ANG BAG-O/UNCOMMENTED! Para ma-scan ang templates sulod sa 'theme/templates/'
    ],
    theme: {
      extend: {}, // Extend Tailwind's default theme if needed
    },
    plugins: [
      require('daisyui'), // Integrate DaisyUI plugin (OKAY)
    ],
    // DaisyUI configuration (OKAY, sakto ang themes)
    daisyui: {
      themes: [
        "light",
        "dark",
        "corporate",
        "synthwave", "retro", "cyberpunk", "valentine", "halloween", "forest", "aqua", "lofi", "pastel", "fantasy", "wireframe", "black", "luxury", "dracula", "cmyk", "autumn", "business", "acid", "lemonade", "night", "coffee", "winter", "dim", "nord", "sunset"
      ],
    },
  };
