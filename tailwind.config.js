/** @type {import('tailwindcss').Config} */

const defaultTheme = require('tailwindcss/defaultTheme')

module.exports = {
  content: [
    './everwealth/templates/*.html',
    './everwealth/templates/**/*.html',
    './everwealth/auth/templates/*.html',
    './everwealth/transactions/templates/**/*.html',
    './everwealth/settings/templates/**/*.html',
    './everwealth/users/templates/**/*.html',
    './everwealth/budgets/templates/**/*.html',
    'node_modules/preline/dist/*.js'
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '"Inter var", sans-serif', {fontFeatureSettings: '"ss01"'}
        ],
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('preline/plugin')
  ],
}

