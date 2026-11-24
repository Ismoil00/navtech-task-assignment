import { api } from './baseApi';
import type { ServiceType } from './types';

export const serviceTypesApi = api.injectEndpoints({
  endpoints: (build) => ({
    getServiceTypes: build.query<ServiceType[], void>({
      query: () => ({ url: '/service-types' }),
      providesTags: ['ServiceTypes'],
      // справочник загружается сразу после входа и живёт всю сессию:
      // выпадающие списки на любой странице берут его из store без нового запроса
      keepUnusedDataFor: 24 * 60 * 60,
    }),
  }),
});

export const { useGetServiceTypesQuery } = serviceTypesApi;
