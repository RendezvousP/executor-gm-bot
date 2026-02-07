"use client";

import { FormEvent, useMemo, useState } from "react";
import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  type ChartData,
  type ChartOptions,
  type TooltipItem,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
);

type TrendPoint = {
  dateLabel: string;
  timestamp: number;
  value: number;
};

type TrendsApiSuccess = {
  points: TrendPoint[];
};

type TrendsApiError = {
  error: string;
  details?: string;
};

type TrendsApiResponse = TrendsApiSuccess | TrendsApiError;

function formatXAxisLabel(label: string) {
  return label.replace(/\u2009/g, " ");
}

export default function Home() {
  const [term, setTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [points, setPoints] = useState<TrendPoint[]>([]);
  const [lastTerm, setLastTerm] = useState<string | null>(null);

  const hasResults = points.length > 0;

  const chartData = useMemo<ChartData<"line">>(() => {
    return {
      labels: points.map((point) => formatXAxisLabel(point.dateLabel)),
      datasets: [
        {
          label: "Relative interest (0-100)",
          data: points.map((point) => point.value),
          borderColor: "#2563eb",
          backgroundColor: "rgba(37, 99, 235, 0.2)",
          tension: 0.25,
          pointRadius: 3,
        },
      ],
    };
  }, [points]);

  const chartOptions = useMemo<ChartOptions<"line">>(() => {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            title: (items: TooltipItem<"line">[]) =>
              items?.[0]?.label ?? "Unknown",
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            stepSize: 20,
          },
          title: {
            display: true,
            text: "Relative interest",
          },
        },
        x: {
          ticks: {
            maxRotation: 0,
            minRotation: 0,
            autoSkip: true,
            maxTicksLimit: 12,
          },
        },
      },
    };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmed = term.trim();
    if (!trimmed) {
      setError("Please enter a search term.");
      setPoints([]);
      setLastTerm(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/trends", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ term: trimmed }),
      });

      const payload = (await response.json()) as TrendsApiResponse;

      if (!response.ok) {
        const message =
          "error" in payload
            ? `${payload.error}${
                payload.details ? ` (${payload.details})` : ""
              }`
            : "SearchAPI returned an unexpected response.";
        setError(message);
        setPoints([]);
        setLastTerm(null);
        return;
      }

      if (!("points" in payload)) {
        setError("SearchAPI returned an unexpected response.");
        setPoints([]);
        setLastTerm(null);
        return;
      }

      setPoints(payload.points);
      setLastTerm(trimmed);
    } catch (err) {
      console.error(err);
      setError("Unable to reach the trends service. Please try again.");
      setPoints([]);
      setLastTerm(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-10 px-6 pb-16 pt-12">
        <header className="space-y-3">
          <h1 className="text-3xl font-semibold tracking-tight">
            Google Trends Explorer
          </h1>
          <p className="text-slate-300">
            Enter a topic to see how relative search interest changed over the
            past 12 months. Data is provided by SearchAPI.io.
          </p>
        </header>

        <form
          onSubmit={handleSubmit}
          className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg shadow-slate-900/40"
        >
          <label className="text-sm font-medium text-slate-300" htmlFor="term">
            Search term
          </label>
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              id="term"
              name="term"
              type="text"
              value={term}
              onChange={(event) => setTerm(event.target.value)}
              placeholder="e.g. electric cars"
              className="flex-1 rounded-lg border border-slate-700 bg-slate-950/60 px-4 py-2 text-base text-slate-100 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50"
            />
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-5 py-2 text-base font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-blue-800"
            >
              {loading ? "Fetching…" : "Show trends"}
            </button>
          </div>
          {error && (
            <p className="text-sm text-red-400" role="alert">
              {error}
            </p>
          )}
        </form>

        <section className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg shadow-slate-900/40">
          {loading && !hasResults ? (
            <p className="text-sm text-slate-300">Fetching trend data…</p>
          ) : hasResults ? (
            <div className="flex flex-col gap-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-100">
                  {lastTerm}
                </h2>
                <p className="text-sm text-slate-400">
                  Relative weekly interest, last 12 months.
                </p>
              </div>
              <div className="h-80 w-full">
                <Line data={chartData} options={chartOptions} />
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-300">
              Submit a search term above to visualize its trend.
            </p>
          )}
        </section>
      </div>
    </main>
  );
}

