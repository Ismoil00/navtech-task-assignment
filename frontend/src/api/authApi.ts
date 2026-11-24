import { credentialsReceived, loggedOut } from '../features/auth/authSlice';
import { api } from './baseApi';
import type { TokenResponse, UserRole } from './types';

export interface LoginRequest {
  username: string;
  password: string;
  portal: UserRole;
}

export const authApi = api.injectEndpoints({
  endpoints: (build) => ({
    login: build.mutation<TokenResponse, LoginRequest>({
      query: (body) => ({ url: '/auth/login', method: 'POST', data: body }),
      async onQueryStarted(_, { dispatch, queryFulfilled }) {
        const { data } = await queryFulfilled;
        dispatch(credentialsReceived(data));
      },
    }),
    logout: build.mutation<void, void>({
      query: () => ({ url: '/auth/logout', method: 'POST' }),
      async onQueryStarted(_, { dispatch, queryFulfilled }) {
        // выходим локально в любом случае, даже если сервер недоступен
        await queryFulfilled.catch(() => undefined);
        dispatch(loggedOut());
      },
    }),
  }),
});

export const { useLoginMutation, useLogoutMutation } = authApi;
