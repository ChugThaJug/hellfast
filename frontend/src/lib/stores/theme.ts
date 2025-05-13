// src/lib/stores/theme.ts
import { writable } from 'svelte/store';
import { browser } from '$app/environment';

// Initialize with a default value that works in SSR
const initialTheme = 'light';

// Create a writable store with the initial value
const theme = writable<'light' | 'dark'>(initialTheme);

// Toggle the theme
function toggleTheme() {
  theme.update(current => {
    const newTheme = current === 'light' ? 'dark' : 'light';
    
    // Only try to access localStorage in the browser
    if (browser) {
      localStorage.setItem('theme', newTheme);
      document.documentElement.classList.toggle('dark', newTheme === 'dark');
    }
    
    return newTheme;
  });
}

// Initialize the theme from localStorage when in browser
if (browser) {
  // Check local storage or system preference
  const savedTheme = localStorage.getItem('theme');
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  const initialValue = savedTheme 
    ? savedTheme 
    : systemPrefersDark 
      ? 'dark' 
      : 'light';
  
  theme.set(initialValue as 'light' | 'dark');
  document.documentElement.classList.toggle('dark', initialValue === 'dark');
}

export { theme, toggleTheme };