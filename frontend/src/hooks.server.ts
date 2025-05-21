// Skip SSR for all routes
export const handle = async ({ event, resolve }) => {
  return resolve(event, {
    ssr: false // Disable SSR for all routes
  });
};

// Required for Svelte 5
export function handleError({ error, event }) {
  return {
    message: 'Server error!'
  };
}