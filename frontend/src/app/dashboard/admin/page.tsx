'use client'

import { useQuery } from '@tanstack/react-query'

import { api } from '@/lib/api'

type AdminStats = {
  total_users: number
  total_farms: number
  total_predictions: number
  open_risks: number
  system_health: string
  generated_at: string
  recent_snapshots: Array<{
    id: string
    farm_id: string
    source: string
    ndvi: number
    drought_risk_score: number
    captured_at: string
  }>
}

export default function AdminDashboardPage() {
  const statsQuery = useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: async () => {
      const response = await api.get<AdminStats>('/api/v1/admin/dashboard')
      return response.data
    },
  })

  const stats = statsQuery.data

  return (
    <main className="mx-auto max-w-4xl space-y-6 px-6 py-8">
      <h1 className="text-2xl font-semibold">Admin Dashboard</h1>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border bg-white p-4">
          <p className="text-sm text-slate-500">Users</p>
          <p className="text-3xl font-semibold">{stats?.total_users ?? '--'}</p>
        </div>
        <div className="rounded-xl border bg-white p-4">
          <p className="text-sm text-slate-500">Farms</p>
          <p className="text-3xl font-semibold">{stats?.total_farms ?? '--'}</p>
        </div>
        <div className="rounded-xl border bg-white p-4">
          <p className="text-sm text-slate-500">Predictions</p>
          <p className="text-3xl font-semibold">{stats?.total_predictions ?? '--'}</p>
        </div>
        <div className="rounded-xl border bg-white p-4">
          <p className="text-sm text-slate-500">Open Risks</p>
          <p className="text-3xl font-semibold">{stats?.open_risks ?? '--'}</p>
        </div>
      </div>
      <div className="rounded-xl border bg-white p-4">
        <p className="text-sm text-slate-500">System Health</p>
        <p className="text-2xl font-semibold capitalize text-emerald-700">
          {stats?.system_health ?? '--'}
        </p>
        {stats?.generated_at ? (
          <p className="text-xs text-slate-500">Last updated {stats.generated_at}</p>
        ) : null}
      </div>
      {stats?.recent_snapshots?.length ? (
        <div className="rounded-xl border bg-white p-4">
          <h2 className="mb-2 text-lg font-medium">Recent snapshots</h2>
          <ul className="divide-y text-sm">
            {stats.recent_snapshots.map((s) => (
              <li key={s.id} className="flex items-center justify-between py-2">
                <span className="font-mono text-xs text-slate-500">{s.id}</span>
                <span className="text-xs text-slate-500">
                  NDVI {s.ndvi.toFixed(2)} • drought {s.drought_risk_score.toFixed(2)} • {s.source}
                </span>
                <span className="text-xs text-slate-500">{s.captured_at}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {statsQuery.isError ? (
        <p className="text-sm text-red-600">Unable to load admin metrics.</p>
      ) : null}
    </main>
  )
}
