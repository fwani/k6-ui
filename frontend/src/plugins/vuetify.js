import { createVuetify } from 'vuetify'

export default createVuetify({
  defaults: {
    VTextField: { density: 'compact' },
    VSelect: { density: 'compact' },
    VTextarea: { density: 'compact' },
  },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: {
          primary: '#1565C0',
          secondary: '#424242',
          error: '#B00020',
          success: '#2E7D32',
          warning: '#ED6C02',
          info: '#0288D1',
          background: '#FFFFFF',
          surface: '#FFFFFF',
        },
      },
    },
  },
})
