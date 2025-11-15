import axios from "axios";

declare module "axios" {
  // eslint-disable-next-line @typescript-eslint/consistent-type-definitions
  interface InternalAxiosRequestConfig {
    _retry?: boolean;
  }
}

import { useAuthStore } from "@/hooks/useAuth";

const baseURL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export const api = axios.create({
  baseURL,
  withCredentials: true,
});

const refreshClient = axios.create({
  baseURL,
  withCredentials: true,
});

let isRefreshing = false;
const pendingQueue: Array<(success: boolean) => void> = [];

function enqueue(callback: (success: boolean) => void) {
  pendingQueue.push(callback);
}

function flushQueue(success: boolean) {
  while (pendingQueue.length > 0) {
    const callback = pendingQueue.shift();
    callback?.(success);
  }
}

function shouldAttemptRefresh(url?: string) {
  if (!url) {
    return false;
  }
  const authPaths = ["/auth/login", "/auth/register", "/auth/logout", "/auth/refresh"];
  return !authPaths.some((path) => url.endsWith(path));
}

function redirectToLogin() {
  if (typeof window === "undefined") {
    return;
  }

  const { pathname } = window.location;
  if (pathname === "/auth/login") {
    return;
  }

  window.location.href = "/auth/login";
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { response, config } = error;
    if (response?.status === 401 && shouldAttemptRefresh(config?.url) && config && !config._retry) {
      if (isRefreshing) {
        await new Promise<void>((resolve, reject) => {
          enqueue((success) => {
            if (success) {
              resolve();
            } else {
              reject(error);
            }
          });
        });
        config._retry = true;
        return api(config);
      }

      config._retry = true;
      isRefreshing = true;
      try {
        await refreshClient.post("/auth/refresh");
        flushQueue(true);
        return api(config);
      } catch (refreshError) {
        useAuthStore.getState().clearUser();
        flushQueue(false);
        redirectToLogin();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    if (response?.status === 401) {
      useAuthStore.getState().clearUser();
      redirectToLogin();
    }
    return Promise.reject(error);
  },
);
