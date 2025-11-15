export const AUTH_PUBLIC_ROUTES = ["/auth/login", "/auth/register"] as const;

export function isAuthPublicRoute(pathname: string | null | undefined): boolean {
  if (!pathname) {
    return false;
  }

  const normalized = pathname.endsWith("/") && pathname !== "/" ? pathname.slice(0, -1) : pathname;
  return AUTH_PUBLIC_ROUTES.some(
    (route) => normalized === route || normalized.startsWith(`${route}/`),
  );
}

export const AUTH_PUBLIC_ENDPOINTS = [
  "/auth/login",
  "/auth/register",
  "/auth/logout",
  "/auth/refresh",
] as const;

export function isAuthPublicEndpoint(url: string | undefined): boolean {
  if (!url) {
    return false;
  }

  let candidate = url;
  if (!candidate.startsWith("/")) {
    try {
      candidate = new URL(candidate).pathname;
    } catch {
      candidate = `/${candidate}`;
    }
  }

  const normalized = candidate.endsWith("/") && candidate !== "/" ? candidate.slice(0, -1) : candidate;
  return AUTH_PUBLIC_ENDPOINTS.some(
    (endpoint) => normalized === endpoint || normalized.endsWith(endpoint),
  );
}

