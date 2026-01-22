export type Borough = {
  id: number;
  name: string;
};

export type BoroughDetail = Borough & {
  total_area: number;
  geometry: any | null;
};

export type CoreScore = {
  borough_id: number;
  borough_name: string;
  percent_explored: number;
  total_area: number;
  unveiled_area: number;
};

// In Expo you can optionally replace this with an env-driven value
// (e.g., EXPO_PUBLIC_API_BASE_URL) via `app.config`.
const API_BASE_URL = "http://10.17.127.104:8000";

async function request<T>(
  path: string,
  options: RequestInit & { userId?: string } = {}
): Promise<T> {
  const { userId, headers, ...rest } = options;
  const url = `${API_BASE_URL}${path}`;

  console.log("API request →", {
    url,
    method: rest.method ?? "GET",
    hasBody: !!rest.body,
    userId,
  });

  let res: Response;
  try {
    res = await fetch(url, {
      ...rest,
      headers: {
        "Content-Type": "application/json",
        ...(headers || {}),
        ...(userId ? { "X-User-Id": userId } : {}),
      },
    });
  } catch (err: any) {
    console.error("Network error during fetch", err);
    throw new Error(
      `Network request failed: ${err?.message ?? String(err ?? "unknown error")}`
    );
  }

  console.log("API response ←", {
    url,
    status: res.status,
    ok: res.ok,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "<failed to read body>");
    console.error("API error body", text);
    throw new Error(`API error ${res.status}: ${text}`);
  }

  return (await res.json()) as T;
}

export async function getHealth() {
  return request<{ status: string }>("/health");
}

export async function getBoroughs(): Promise<Borough[]> {
  return request<Borough[]>("/boroughs");
}

export async function getBoroughDetail(
  boroughId: number
): Promise<BoroughDetail> {
  return request<BoroughDetail>(`/boroughs/${boroughId}`);
}

export async function createOrUpdateUser(opts: {
  id: string;
  chosenBoroughId: number | null;
}): Promise<{ id: string; chosen_borough_id: number | null }> {
  return request("/users", {
    method: "POST",
    body: JSON.stringify({
      id: opts.id,
      chosen_borough_id: opts.chosenBoroughId,
    }),
  });
}

export async function getCoreScore(userId: string): Promise<CoreScore> {
  return request<CoreScore>("/stats/core-score", { userId });
}


