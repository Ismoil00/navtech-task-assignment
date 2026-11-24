import { api } from './baseApi';
import type { Application, ApplicationListItem, ApplicationStatus, Page } from './types';

export interface MyApplicationsParams {
  status?: ApplicationStatus | null;
  page: number;
  pageSize: number;
}

export const applicationsApi = api.injectEndpoints({
  endpoints: (build) => ({
    listMyApplications: build.query<Page<ApplicationListItem>, MyApplicationsParams>({
      query: ({ status, page, pageSize }) => ({
        url: '/applications',
        params: { status: status ?? undefined, page, page_size: pageSize },
      }),
      providesTags: ['MyApplications'],
    }),
    getMyApplication: build.query<Application, string>({
      query: (id) => ({ url: `/applications/${id}` }),
      providesTags: (_result, _error, id) => [{ type: 'Application', id }],
    }),
  }),
});

export const { useListMyApplicationsQuery, useGetMyApplicationQuery } = applicationsApi;
