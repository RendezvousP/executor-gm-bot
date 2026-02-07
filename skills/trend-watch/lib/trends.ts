const SEARCH_API_URL = "https://www.searchapi.io/api/v1/search";

export type TrendPoint = {
  dateLabel: string;
  timestamp: number;
  value: number;
};

export class SearchApiError extends Error {
  status: number;
  details?: string;

  constructor(message: string, status: number, details?: string) {
    super(message);
    this.name = "SearchApiError";
    this.status = status;
    this.details = details;
  }
}

type FetchTrendsParams = {
  term: string;
  geo?: string;
  category?: string;
  apiKey?: string;
};

type TimelineDataPoint = {
  date: string;
  timestamp: string;
  values?: Array<{
    value?: string;
    extracted_value?: number;
  }>;
};

type TrendsResponse = {
  interest_over_time?: {
    timeline_data?: TimelineDataPoint[];
  };
  message?: string;
  error?: string;
};

const THIN_SPACE_PATTERN = /\u2009/g;

export async function fetchTrendSeries({
  term,
  geo,
  category,
  apiKey,
}: FetchTrendsParams): Promise<TrendPoint[]> {
  const resolvedKey = apiKey ?? process.env.SEARCH_API_KEY;

  if (!resolvedKey) {
    throw new SearchApiError(
      "SEARCH_API_KEY is not configured on the server.",
      500,
    );
  }

  const trimmedTerm = term.trim();

  if (!trimmedTerm) {
    throw new SearchApiError("Search term is required.", 400);
  }

  const params = new URLSearchParams({
    engine: "google_trends",
    q: trimmedTerm,
    date: "now 12-m",
    data_type: "TIMESERIES",
  });

  if (geo?.trim()) {
    params.set("geo", geo.trim());
  }

  if (category?.trim()) {
    params.set("cat", category.trim());
  }

  let response: Response;

  try {
    response = await fetch(`${SEARCH_API_URL}?${params.toString()}`, {
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${resolvedKey}`,
      },
    });
  } catch (error) {
    const details =
      error instanceof Error ? error.message : "Unknown network error.";

    throw new SearchApiError(
      "Unable to reach SearchAPI.",
      502,
      details || undefined,
    );
  }

  if (!response.ok) {
    let details: string | undefined;

    try {
      const payload = (await response.json()) as TrendsResponse;
      details = payload.error ?? payload.message;
    } catch {
      details = undefined;
    }

    throw new SearchApiError(
      "Failed to retrieve trends data from SearchAPI.",
      response.status,
      details,
    );
  }

  const data = (await response.json()) as TrendsResponse;
  const timelineData = data.interest_over_time?.timeline_data ?? [];

  return timelineData.map((entry) => {
    const timestampSeconds = Number(entry.timestamp);
    const derivedTimestamp = Number.isFinite(timestampSeconds)
      ? timestampSeconds * 1000
      : Date.parse(entry.date);

    const firstValue = entry.values?.[0];
    const extracted =
      typeof firstValue?.extracted_value === "number"
        ? firstValue.extracted_value
        : Number(firstValue?.value ?? 0);

    return {
      dateLabel: entry.date.replace(THIN_SPACE_PATTERN, " "),
      timestamp: Number.isFinite(derivedTimestamp)
        ? derivedTimestamp
        : Date.now(),
      value: Number.isFinite(extracted) ? extracted : 0,
    };
  });
}

