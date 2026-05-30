'use client'

import { useQuery } from '@tanstack/react-query'

import { api } from '@/lib/api'

type AdminStats = {
  total_users: number
  total_farms: number
  total_predictions: number
  system_health: string
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
      <div className="grid gap-4 md:grid-cols-2">
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
          <p className="text-sm text-slate-500">System Health</p>
          <p className="text-3xl font-semibold capitalize">{stats?.system_health ?? '--'}</p>
        </div>
      </div>
      {statsQuery.isError ? <p className="text-sm text-red-600">Unable to load admin metrics.</p> : null}
    </main>
  )
}
