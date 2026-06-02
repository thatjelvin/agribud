'use client'

import { useQuery } from '@tanstack/react-query'

import { api } from '@/lib/api'

type CropBreakdown = { crop_type: string; farm_count: number }
type RecentSnapshot = {
  id: string
  farm_id: string
  ndvi: number
  captured_at: string
}
type Overview = {
  total_farms: number
  total_area_ha: number
  total_yield_predictions: number
  avg_predicted_yield_ton_ha: number | null
  crop_breakdown: CropBreakdown[]
  recent_snapshots: RecentSnapshot[]
  generated_at: string
}

export default function AgribusinessDashboardPage() {
  const overviewQuery = useQuery({
    queryKey: ['agribusiness-overview'],
    queryFn: async () => {
      const response = await api.get<Overview>('/api/v1/agribusiness/overview')
      return response.data
    },
  })

  const overview = overviewQuery.data
  return (
    <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <header>
        <h1 className="text-2xl font-semibold">Agribusiness Overview</h1>
        <p className="text-sm text-slate-600">
          Aggregated farm, yield, and supply visibility across the platform.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Total farms" value={overview?.total_farms} />
        <Stat label="Total area (ha)" value={overview?.total_area_ha} decimals={1} />
        <Stat label="Yield predictions" value={overview?.total_yield_predictions} />
        <Stat
          label="Avg predicted (t/ha)"
          value={overview?.avg_predicted_yield_ton_ha}
          decimals={2}
        />
      </section>

      <section className="rounded-xl border bg-white p-4">
        <h2 className="mb-2 text-lg font-medium">Crops on the platform</h2>
        {overview?.crop_breakdown && overview.crop_breakdown.length > 0 ? (
          <table className="w-full text-sm">
            <thead className="text-left text-slate-500">
              <tr>
                <th className="py-1">Crop</th>
                <th>Farms</th>
              </tr>
            </thead>
            <tbody>
              {overview.crop_breakdown.map((row) => (
                <tr key={row.crop_type} className="border-t">
                  <td className="py-1 capitalize">{row.crop_type}</td>
                  <td>{row.farm_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-sm text-slate-500">No farms yet.</p>
        )}
      </section>

      <section className="rounded-xl border bg-white p-4">
        <h2 className="mb-2 text-lg font-medium">Recent snapshots</h2>
        <ul className="space-y-1 text-sm">
          {overview?.recent_snapshots?.map((snap) => (
            <li key={snap.id} className="flex justify-between border-t py-1">
              <span className="font-mono text-xs text-slate-500">
                {snap.id.slice(0, 8)}…
              </span>
              <span>NDVI {snap.ndvi.toFixed(2)}</span>
              <span className="text-xs text-slate-500">
                {new Date(snap.captured_at).toLocaleString()}
              </span>
            </li>
          ))}
        </ul>
      </section>

      {overviewQuery.isError ? (
        <p className="text-sm text-red-600">Unable to load overview.</p>
      ) : null}
    </main>
  )
}

function Stat({
  label,
  value,
  decimals = 0,
}: {
  label: string
  value: number | null | undefined
  decimals?: number
}) {
  const display = value == null ? '—' : value.toFixed(decimals)
  return (
    <div className="rounded-xl border bg-white p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{display}</div>
    </div>
  )
}
