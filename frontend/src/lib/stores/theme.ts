// frontend/src/lib/stores/theme.ts
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
    console.log(`Toggling theme from ${current} to ${newTheme}`);
    
    // Only try to access localStorage in the browser
    if (browser) {
      try {
        localStorage.setItem('theme', newTheme);
        document.documentElement.classList.toggle('dark', newTheme === 'dark');
        console.log(`Theme saved to localStorage: ${newTheme}`);
      } catch (error) {
        console.error("Error updating theme:", error);
      }
    }
    
    return newTheme;
  });
}

// Initialize the theme from localStorage when in browser
if (browser) {
  try {
    console.log("Initializing theme from browser preferences");
    // Check local storage or system preference
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    const initialValue = savedTheme 
      ? savedTheme 
      : systemPrefersDark 
        ? 'dark' 
        : 'light';
    
    console.log(`Theme initialized to: ${initialValue}`);
    theme.set(initialValue as 'light' | 'dark');
    document.documentElement.classList.toggle('dark', initialValue === 'dark');
  } catch (error) {
    console.error("Error initializing theme:", error);
  }
}

export { theme, toggleTheme };