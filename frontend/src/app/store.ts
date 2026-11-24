import { combineSlices, configureStore, createListenerMiddleware } from '@reduxjs/toolkit';

import { api } from '../api/baseApi';
import { connectSession } from '../api/http';
import { serviceTypesApi } from '../api/serviceTypesApi';
import { authSlice, credentialsReceived, loggedOut } from '../features/auth/authSlice';

const rootReducer = combineSlices(authSlice, api);

const listeners = createListenerMiddleware();

// Сразу после входа (или восстановления сессии) загружаем справочник услуг:
// он хранится в store и доступен всем страницам без повторных запросов.
listeners.startListening({
  actionCreator: credentialsReceived,
  effect: (_, { dispatch }) => {
    dispatch(serviceTypesApi.util.prefetch('getServiceTypes', undefined, { force: false }));
  },
});

// При выходе очищаем весь кеш API, чтобы следующий пользователь не увидел чужие данные
listeners.startListening({
  actionCreator: loggedOut,
  effect: (_, { dispatch }) => {
    dispatch(api.util.resetApiState());
  },
});

export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefault) => getDefault().prepend(listeners.middleware).concat(api.middleware),
});

connectSession({
  getAccessToken: () => store.getState().auth.accessToken,
  onRefreshed: (tokens) => store.dispatch(credentialsReceived(tokens)),
  onSessionLost: () => store.dispatch(loggedOut()),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
