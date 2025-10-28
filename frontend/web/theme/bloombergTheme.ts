export const bloombergDarkTheme = {
  colors: {
    bgBase: "#0A0C10",
    bgPanel: "#111318",
    bgAlt: "#161923",
    borderMuted: "#1C1F26",
    borderActive: "#29448A",
    textPrimary: "#E6E9F2",
    textSecondary: "#8C96A8",
    accentNeutral: "#4C7DE5",
    accentBull: "#4BD37B",
    accentBear: "#F45B69",
    stateWarning: "#F7B500"
  },
  typography: {
    fontPrimary: '"Inter", "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif',
    fontMono: '"IBM Plex Mono", monospace'
  },
  layout: {
    maxWidth: 1440,
    gridGutter: 24
  }
} as const;

export type BloombergDarkTheme = typeof bloombergDarkTheme;
