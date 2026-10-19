import { cookies } from "next/headers";

import type { User } from "@/lib/auth-api";

const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

async function serverApiRequest<T>(path: string): Promise<T> {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("access_token");

  if (!accessToken) {
    throw new Error("No authenticated session is available.");
  }

  const response = await fetch(`${backendUrl}${path}`, {
    headers: {
      Cookie: `access_token=${accessToken.value}`,
    },
    cache: "no-store",
  });

  if (response.status === 401) {
    throw new Error("Your session has expired.");
  }

  if (!response.ok) {
    throw new Error(`Backend request failed with status ${response.status}.`);
  }

  return (await response.json()) as T;
}

export async function getCurrentUser(): Promise<User | null> {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("access_token");

  if (!accessToken) {
    return null;
  }

  const response = await fetch(`${backendUrl}/api/v1/auth/me`, {
    headers: {
      Cookie: `access_token=${accessToken.value}`,
    },
    cache: "no-store",
  });

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Unable to verify the current session.");
  }

  return (await response.json()) as User;
}

export { serverApiRequest };
