import { NextResponse } from "next/server";
import { fetchTrendSeries, SearchApiError } from "@/lib/trends";

type TrendsRequestBody = {
  term?: string;
  geo?: string;
  category?: string;
};

export async function POST(request: Request) {
  let payload: TrendsRequestBody;

  try {
    payload = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Request body must be valid JSON." },
      { status: 400 },
    );
  }

  const term = payload.term ?? "";

  try {
    const points = await fetchTrendSeries({
      term,
      geo: payload.geo,
      category: payload.category,
    });

    return NextResponse.json({ points });
  } catch (error) {
    if (error instanceof SearchApiError) {
      return NextResponse.json(
        {
          error: error.message,
          details: error.details,
        },
        { status: error.status },
      );
    }

    console.error("Unexpected error in trends API:", error);
    return NextResponse.json(
      { error: "Unexpected server error." },
      { status: 500 },
    );
  }
}

