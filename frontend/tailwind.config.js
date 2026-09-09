export default {
  content: ['./index.html','./admin.html','./src/**/*.{vue,js}'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter','sans-serif'] },
      colors: {
        green:  { DEFAULT:'#1F7A4C', dark:'#155c38', light:'#E8F5EE', mid:'#2d9e65' },
        blue:   { DEFAULT:'#2563EB', dark:'#1d4ed8', light:'#EFF6FF' },
        amber:  { DEFAULT:'#D97706', light:'#FFFBEB' },
        red:    { DEFAULT:'#EF4444', light:'#FEF2F2' },
        purple: { DEFAULT:'#7C3AED', light:'#F5F3FF' },
        slate:  { DEFAULT:'#1E293B', mid:'#475569', light:'#94A3B8', xlight:'#CBD5E1' },
        ig1:    '#F58529', ig2: '#DD2A7B', ig3: '#8134AF',
        border: '#E2E8F0', surface: '#F8FAFC',
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,.06),0 1px 2px rgba(0,0,0,.04)',
        md:   '0 4px 12px rgba(0,0,0,.08)',
        lg:   '0 10px 40px rgba(0,0,0,.12)',
        green:'0 4px 14px rgba(31,122,76,.3)',
      },
      borderRadius: { xl: '14px', '2xl': '18px' }
    }
  },
  plugins: []
}
