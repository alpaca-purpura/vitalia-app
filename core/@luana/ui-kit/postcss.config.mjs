/**
 * PostCSS — Tailwind v4 for @luana/ui-kit Storybook (story core-ds-foundation T-2).
 * The @tailwindcss/postcss plugin processes the @import "tailwindcss" + @theme/@source
 * directives in .storybook/preview.css. Without it those directives ship as literal text
 * and no utility classes are generated (the bug-origin pattern noted in vitalia globals.css).
 */
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
