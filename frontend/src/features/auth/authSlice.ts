import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

import type { TokenResponse, User } from '../../api/types';

/** checking — при загрузке страницы восстанавливаем сессию по cookie. */
export type SessionStatus = 'checking' | 'authenticated' | 'anonymous';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  status: SessionStatus;
}

const initialState: AuthState = { user: null, accessToken: null, status: 'checking' };

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    credentialsReceived(state, action: PayloadAction<TokenResponse>) {
      state.user = action.payload.user;
      state.accessToken = action.payload.access_token;
      state.status = 'authenticated';
    },
    loggedOut(state) {
      state.user = null;
      state.accessToken = null;
      state.status = 'anonymous';
    },
  },
  selectors: {
    selectUser: (state) => state.user,
    selectAccessToken: (state) => state.accessToken,
    selectSessionStatus: (state) => state.status,
  },
});

export const { credentialsReceived, loggedOut } = authSlice.actions;
export const { selectUser, selectAccessToken, selectSessionStatus } = authSlice.selectors;
