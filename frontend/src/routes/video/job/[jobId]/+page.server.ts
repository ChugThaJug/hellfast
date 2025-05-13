// frontend/src/routes/video/job/[jobId]/+page.server.ts
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params }) => {
  return {
    jobId: params.jobId
  };
};