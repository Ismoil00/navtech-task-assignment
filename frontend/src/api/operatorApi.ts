import { api } from './baseApi';
import type { Application, ApplicationListItem, ApplicationStatus, DecisionAction, Page } from './types';

export interface QueueParams {
  status: ApplicationStatus | null;
  serviceTypeId: number | null;
  page: number;
  pageSize: number;
}

export const operatorApi = api.injectEndpoints({
  endpoints: (build) => ({
    listQueue: build.query<Page<ApplicationListItem>, QueueParams>({
      query: ({ status, serviceTypeId, page, pageSize }) => ({
        url: '/operator/applications',
        params: {
          status: status ?? undefined,
          service_type_id: serviceTypeId ?? undefined,
          page,
          page_size: pageSize,
        },
      }),
      providesTags: ['Queue'],
    }),
    getOperatorApplication: build.query<Application, string>({
      query: (id) => ({ url: `/operator/applications/${id}` }),
      providesTags: (_result, _error, id) => [{ type: 'Application', id }],
    }),
    decide: build.mutation<Application, { id: string; action: DecisionAction; comment: string | null }>({
      query: ({ id, action, comment }) => ({
        url: `/operator/applications/${id}/decision`,
        method: 'POST',
        data: { action, comment },
      }),
      invalidatesTags: (_result, _error, { id }) => [{ type: 'Application', id }, 'Queue'],
    }),
  }),
});

export const { useListQueueQuery, useGetOperatorApplicationQuery, useDecideMutation } = operatorApi;
