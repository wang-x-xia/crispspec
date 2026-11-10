import { createContext, useContext } from 'react';

export type Theme = 'dark' | 'light';

export interface ThemeContextValue {
  theme: Theme;
  toggle: () => void;
}

export const ThemeContext = createContext<ThemeContextValue>({ theme: 'dark', toggle: () => undefined });

/** The current theme and a toggle for it. */
export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext);
}
