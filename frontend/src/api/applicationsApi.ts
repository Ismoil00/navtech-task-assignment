import type { AppDispatch } from '../app/store';
import { api } from './baseApi';
import type {
  Application,
  ApplicationInput,
  ApplicationListItem,
  ApplicationStatus,
  Page,
} from './types';

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
    createApplication: build.mutation<Application, ApplicationInput>({
      query: (body) => ({ url: '/applications', method: 'POST', data: body }),
      invalidatesTags: ['MyApplications'],
    }),
    updateApplication: build.mutation<Application, { id: string; changes: Partial<ApplicationInput> }>({
      query: ({ id, changes }) => ({ url: `/applications/${id}`, method: 'PATCH', data: changes }),
      invalidatesTags: (_result, _error, { id }) => [{ type: 'Application', id }, 'MyApplications'],
    }),
    submitApplication: build.mutation<Application, string>({
      query: (id) => ({ url: `/applications/${id}/submit`, method: 'POST' }),
      invalidatesTags: (_result, _error, id) => [{ type: 'Application', id }, 'MyApplications'],
    }),
    deleteApplication: build.mutation<void, string>({
      query: (id) => ({ url: `/applications/${id}`, method: 'DELETE' }),
      invalidatesTags: ['MyApplications'],
    }),
  }),
});

/**
 * Кладёт заявку из ответа сервера в кеш карточки и обновляет список.
 * Нужно для запросов, которые идут мимо RTK Query (загрузка файла, оплата).
 */
export function cacheApplication(dispatch: AppDispatch, application: Application): void {
  dispatch(applicationsApi.util.upsertQueryData('getMyApplication', application.id, application));
  dispatch(applicationsApi.util.invalidateTags(['MyApplications']));
}

export const {
  useListMyApplicationsQuery,
  useGetMyApplicationQuery,
  useCreateApplicationMutation,
  useUpdateApplicationMutation,
  useSubmitApplicationMutation,
  useDeleteApplicationMutation,
} = applicationsApi;
