/** @type {import('tailwindcss').Config} */

module.exports = {
  content: [
    './everwealth/templates/**/*.html',
    './everwealth/static/src/**/*.js',
  ],
  daisyui: {
    themes: ['corporate', 'sunset'],
    darkTheme: 'sunset',
  },
  plugins: [
    require('daisyui')
  ],
}
