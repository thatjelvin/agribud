'use client'

import { useQuery } from '@tanstack/react-query'

import { api } from '@/lib/api'

type HighRiskFarm = { farm_name: string; avg_drought_risk: number }
type Overview = {
  total_farms: number
  total_yield_predictions: number
  avg_predicted_yield_ton_ha: number | null
  avg_confidence_score: number | null
  open_risks: number
  severity_breakdown: Record<string, number>
  high_risk_farms: HighRiskFarm[]
  generated_at: string
}

const SEVERITY_ORDER = ['critical', 'high', 'medium', 'low']

export default function LenderDashboardPage() {
  const overviewQuery = useQuery({
    queryKey: ['lender-overview'],
    queryFn: async () => {
      const response = await api.get<Overview>('/api/v1/lender/overview')
      return response.data
    },
  })

  const overview = overviewQuery.data

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <header>
        <h1 className="text-2xl font-semibold">Lender Portfolio</h1>
        <p className="text-sm text-slate-600">
          Yield forecasts and risk exposure for credit decisions.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Farms" value={overview?.total_farms} />
        <Stat label="Yield predictions" value={overview?.total_yield_predictions} />
        <Stat
          label="Avg predicted (t/ha)"
          value={overview?.avg_predicted_yield_ton_ha}
          decimals={2}
        />
        <Stat
          label="Avg confidence"
          value={overview?.avg_confidence_score}
          decimals={2}
        />
      </section>

      <section className="rounded-xl border bg-white p-4">
        <h2 className="mb-2 text-lg font-medium">Open risks ({overview?.open_risks ?? 0})</h2>
        <div className="flex flex-wrap gap-2 text-sm">
          {SEVERITY_ORDER.map((sev) => (
            <span
              key={sev}
              className="rounded-md border bg-slate-50 px-2 py-1 capitalize"
            >
              {sev}: {overview?.severity_breakdown?.[sev] ?? 0}
            </span>
          ))}
        </div>
      </section>

      <section className="rounded-xl border bg-white p-4">
        <h2 className="mb-2 text-lg font-medium">High drought-risk farms</h2>
        {overview?.high_risk_farms && overview.high_risk_farms.length > 0 ? (
          <table className="w-full text-sm">
            <thead className="text-left text-slate-500">
              <tr>
                <th className="py-1">Farm</th>
                <th>Avg drought risk</th>
              </tr>
            </thead>
            <tbody>
              {overview.high_risk_farms.map((row) => (
                <tr key={row.farm_name} className="border-t">
                  <td className="py-1">{row.farm_name}</td>
                  <td>{row.avg_drought_risk.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-sm text-slate-500">No risk data yet.</p>
        )}
      </section>

      {overviewQuery.isError ? (
        <p className="text-sm text-red-600">Unable to load portfolio.</p>
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
