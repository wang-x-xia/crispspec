import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

import { ThemeContext, type Theme } from './theme';

/** Holds the colour theme and keeps it in the document body. */
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    const stored = window.localStorage.getItem('crispspec-theme');
    return stored === 'light' ? 'light' : 'dark';
  });

  useEffect(() => {
    document.body.classList.toggle('light', theme === 'light');
    window.localStorage.setItem('crispspec-theme', theme);
  }, [theme]);

  const value = useMemo(
    () => ({ theme, toggle: () => setTheme((current) => (current === 'dark' ? 'light' : 'dark')) }),
    [theme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
