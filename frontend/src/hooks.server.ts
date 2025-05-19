// Skip SSR for all routes
export const handle = async ({ event, resolve }) => {
  return resolve(event, {
    ssr: false // Disable SSR for all routes
  });
};
