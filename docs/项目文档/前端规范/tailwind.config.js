/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    './pages/**/*.{js,jsx,ts,tsx}',
    './components/**/*.{js,jsx,ts,tsx}',
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      // 品牌色
      colors: {
        bloomberg: {
          black: '#000000',
          orange: '#FF6600',
          amber: '#FFA500',
        },
        // 背景色
        background: {
          primary: '#0D0D0D',
          secondary: '#1A1A1A',
          tertiary: '#2A2A2A',
          card: '#1C1C1C',
        },
        // 市场数据色
        market: {
          positive: '#00C805',
          negative: '#FF3347',
          neutral: '#8C8C8C',
        },
        // 资产类别色
        asset: {
          stock: '#3B82F6',
          bond: '#A855F7',
          commodity: '#EAB308',
          forex: '#06B6D4',
        },
        // 文字色
        text: {
          primary: '#FFFFFF',
          secondary: '#A0A0A0',
          tertiary: '#707070',
          disabled: '#505050',
        },
        // 边框色
        border: {
          primary: 'rgba(255, 255, 255, 0.1)',
          secondary: 'rgba(255, 255, 255, 0.05)',
        },
      },
      
      // 字体家族
      fontFamily: {
        mono: ['Bloomberg Mono', 'SF Mono', 'Consolas', 'Courier New', 'monospace'],
        heading: ['Inter', 'system-ui', 'sans-serif'],
        data: ['IBM Plex Mono', 'Roboto Mono', 'monospace'],
        body: ['Inter', 'system-ui', 'sans-serif'],
      },
      
      // 字体大小
      fontSize: {
        'data-lg': ['24px', { lineHeight: '1.2' }],
        'data-md': ['18px', { lineHeight: '1.2' }],
        'data-sm': ['14px', { lineHeight: '1.2' }],
      },
      
      // 间距
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      
      // 容器最大宽度
      maxWidth: {
        '8xl': '88rem',
        '9xl': '96rem',
      },
      
      // 断点
      screens: {
        'xs': '480px',
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px',
        '3xl': '1920px',
      },
      
      // 阴影
      boxShadow: {
        'dark-sm': '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
        'dark-md': '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
        'dark-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
        'dark-xl': '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
      },
      
      // 过渡时间
      transitionDuration: {
        '0': '0ms',
        '150': '150ms',
        '200': '200ms',
        '250': '250ms',
        '350': '350ms',
      },
      
      // 动画
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'data-update': 'dataUpdate 0.5s ease-out',
        'flash': 'flash 0.5s ease-in-out',
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-in': 'slideIn 0.2s ease-out',
      },
      
      // 动画关键帧
      keyframes: {
        dataUpdate: {
          '0%': { backgroundColor: 'rgba(255, 102, 0, 0.3)' },
          '100%': { backgroundColor: 'transparent' },
        },
        flash: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        slideIn: {
          from: { 
            transform: 'translateY(-10px)',
            opacity: '0',
          },
          to: { 
            transform: 'translateY(0)',
            opacity: '1',
          },
        },
      },
      
      // 边框圆角
      borderRadius: {
        'none': '0',
        'sm': '2px',
        DEFAULT: '4px',
        'md': '6px',
        'lg': '8px',
        'xl': '12px',
      },
      
      // 背景图案
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'loading-gradient': 'linear-gradient(90deg, rgba(255, 255, 255, 0.05) 25%, rgba(255, 255, 255, 0.1) 50%, rgba(255, 255, 255, 0.05) 75%)',
      },
      
      // Z-index
      zIndex: {
        '1': '1',
        '10': '10',
        '20': '20',
        '30': '30',
        '40': '40',
        '50': '50',
        'dropdown': '1000',
        'sticky': '1020',
        'fixed': '1030',
        'modal-backdrop': '1040',
        'modal': '1050',
        'popover': '1060',
        'tooltip': '1070',
      },
    },
  },
  plugins: [
    // 添加自定义插件
    function({ addUtilities, addComponents, theme }) {
      // 自定义工具类
      const newUtilities = {
        // 数字等宽
        '.tabular-nums': {
          fontVariantNumeric: 'tabular-nums',
        },
        // 文本截断
        '.text-truncate': {
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        },
        // 多行截断
        '.line-clamp-2': {
          display: '-webkit-box',
          '-webkit-line-clamp': '2',
          '-webkit-box-orient': 'vertical',
          overflow: 'hidden',
        },
        '.line-clamp-3': {
          display: '-webkit-box',
          '-webkit-line-clamp': '3',
          '-webkit-box-orient': 'vertical',
          overflow: 'hidden',
        },
        '.line-clamp-4': {
          display: '-webkit-box',
          '-webkit-line-clamp': '4',
          '-webkit-box-orient': 'vertical',
          overflow: 'hidden',
        },
        // 滚动条隐藏
        '.scrollbar-hide': {
          '-ms-overflow-style': 'none',
          'scrollbar-width': 'none',
          '&::-webkit-scrollbar': {
            display: 'none',
          },
        },
        // 自定义滚动条
        '.scrollbar-dark': {
          '&::-webkit-scrollbar': {
            width: '8px',
            height: '8px',
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: theme('colors.background.secondary'),
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            borderRadius: theme('borderRadius.DEFAULT'),
          },
          '&::-webkit-scrollbar-thumb:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.3)',
          },
        },
      };
      
      // 自定义组件类
      const newComponents = {
        // 数据卡片
        '.data-card': {
          backgroundColor: theme('colors.background.card'),
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: theme('borderRadius.DEFAULT'),
          padding: theme('spacing.4'),
          marginBottom: theme('spacing.4'),
        },
        '.data-card-header': {
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: theme('spacing.3'),
          paddingBottom: theme('spacing.2'),
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        },
        
        // 股票代码标签
        '.ticker-badge': {
          display: 'inline-flex',
          alignItems: 'center',
          padding: `${theme('spacing.1')} ${theme('spacing.3')}`,
          backgroundColor: 'rgba(59, 130, 246, 0.15)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: theme('borderRadius.DEFAULT'),
          fontFamily: theme('fontFamily.data'),
          fontSize: theme('fontSize.sm'),
          fontWeight: theme('fontWeight.semibold'),
          color: theme('colors.asset.stock'),
          letterSpacing: '0.5px',
        },
        
        // 数据表格
        '.data-table': {
          width: '100%',
          borderCollapse: 'separate',
          borderSpacing: '0',
          fontFamily: theme('fontFamily.data'),
          fontSize: theme('fontSize.sm'),
          '& thead': {
            backgroundColor: theme('colors.background.secondary'),
            position: 'sticky',
            top: '0',
            zIndex: '10',
          },
          '& th': {
            padding: `${theme('spacing.3')} ${theme('spacing.4')}`,
            textAlign: 'left',
            fontWeight: theme('fontWeight.semibold'),
            color: theme('colors.text.secondary'),
            borderBottom: '2px solid rgba(255, 255, 255, 0.1)',
          },
          '& td': {
            padding: `${theme('spacing.2')} ${theme('spacing.4')}`,
            borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
          },
          '& tr:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.03)',
          },
          '& .numeric': {
            textAlign: 'right',
            fontVariantNumeric: 'tabular-nums',
          },
        },
        
        // 实时指示器
        '.live-indicator': {
          display: 'inline-flex',
          alignItems: 'center',
          gap: theme('spacing.2'),
          '&::before': {
            content: '""',
            width: '8px',
            height: '8px',
            backgroundColor: theme('colors.market.positive'),
            borderRadius: '50%',
            animation: 'pulse 2s ease-in-out infinite',
          },
        },
        
        // 按钮基础样式
        '.btn': {
          padding: `${theme('spacing.2')} ${theme('spacing.4')}`,
          borderRadius: theme('borderRadius.DEFAULT'),
          fontWeight: theme('fontWeight.medium'),
          fontSize: theme('fontSize.sm'),
          transition: `all ${theme('transitionDuration.200')} ease`,
          cursor: 'pointer',
          border: 'none',
          '&:disabled': {
            cursor: 'not-allowed',
            opacity: '0.5',
          },
        },
        '.btn-primary': {
          backgroundColor: theme('colors.bloomberg.orange'),
          color: 'white',
          '&:hover:not(:disabled)': {
            backgroundColor: '#FF7722',
          },
        },
        '.btn-secondary': {
          backgroundColor: 'transparent',
          color: theme('colors.text.primary'),
          border: '1px solid rgba(255, 255, 255, 0.2)',
          '&:hover:not(:disabled)': {
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            borderColor: 'rgba(255, 255, 255, 0.3)',
          },
        },
        
        // 输入框
        '.input': {
          padding: `${theme('spacing.3')} ${theme('spacing.4')}`,
          backgroundColor: theme('colors.background.secondary'),
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: theme('borderRadius.DEFAULT'),
          color: theme('colors.text.primary'),
          fontSize: theme('fontSize.base'),
          transition: `all ${theme('transitionDuration.200')} ease`,
          '&:focus': {
            outline: 'none',
            borderColor: theme('colors.bloomberg.orange'),
            boxShadow: '0 0 0 3px rgba(255, 102, 0, 0.1)',
          },
          '&::placeholder': {
            color: theme('colors.text.tertiary'),
          },
        },
        
        // 新闻卡片
        '.news-card': {
          backgroundColor: theme('colors.background.card'),
          borderLeft: '3px solid transparent',
          padding: theme('spacing.4'),
          marginBottom: theme('spacing.3'),
          transition: `all ${theme('transitionDuration.200')}`,
          '&:hover': {
            borderLeftColor: theme('colors.bloomberg.orange'),
            backgroundColor: theme('colors.background.secondary'),
          },
        },
        
        // 警报组件
        '.alert': {
          display: 'flex',
          alignItems: 'flex-start',
          gap: theme('spacing.3'),
          padding: theme('spacing.4'),
          borderRadius: theme('borderRadius.DEFAULT'),
          marginBottom: theme('spacing.4'),
        },
        '.alert-warning': {
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          borderLeft: '4px solid ' + theme('colors.warning'),
        },
        '.alert-error': {
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          borderLeft: '4px solid ' + theme('colors.error'),
        },
        '.alert-info': {
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderLeft: '4px solid ' + theme('colors.info'),
        },
      };
      
      addUtilities(newUtilities);
      addComponents(newComponents);
    },
  ],
};
