export type FieldErrors = Record<string, string>;

export class ApiError extends Error {
  status: number;
  fieldErrors: FieldErrors;

  constructor(
    status: number,
    message: string,
    fieldErrors: FieldErrors = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

function parseDetail(detail: unknown): {
  message: string;
  fieldErrors: FieldErrors;
} {
  if (typeof detail === "string") {
    return { message: detail, fieldErrors: {} };
  }

  if (Array.isArray(detail)) {
    const fieldErrors: FieldErrors = {};
    const messages: string[] = [];

    for (const item of detail) {
      if (!item || typeof item !== "object") {
        continue;
      }

      const error = item as { loc?: unknown; msg?: unknown };
      const message = typeof error.msg === "string" ? error.msg : "Invalid value";
      const location = Array.isArray(error.loc) ? error.loc : [];
      const field = location.at(-1);

      if (typeof field === "string") {
        fieldErrors[field] = message;
      }
      messages.push(message);
    }

    return {
      message: messages[0] ?? "The request was invalid.",
      fieldErrors,
    };
  }

  return { message: "The request could not be completed.", fieldErrors: {} };
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(path, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    let body: { detail?: unknown } = {};
    try {
      body = (await response.json()) as { detail?: unknown };
    } catch {
      // Use the status-based fallback below when the response has no JSON body.
    }

    const parsed = parseDetail(body.detail);
    throw new ApiError(response.status, parsed.message, parsed.fieldErrors);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
