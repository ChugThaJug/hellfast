// frontend/src/routes/video/[videoId]/+page.server.ts
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params }) => {
  return {
    videoId: params.videoId
  };
};