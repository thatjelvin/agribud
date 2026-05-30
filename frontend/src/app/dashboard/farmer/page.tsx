'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'

type Farm = {
  id: number
  farm_name: string
  crop_type: string
}

export default function FarmerDashboardPage() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<string | null>(null)
  const farmsQuery = useQuery({
    queryKey: ['farms'],
    queryFn: async () => {
      const response = await api.get<Farm[]>('/api/v1/farms')
      return response.data
    },
  })

  const snapshotMutation = useMutation({
    mutationFn: async (farmId: number) => api.post(`/api/v1/analytics/farms/${farmId}/snapshot`),
    onSuccess: () => farmsQuery.refetch(),
  })

  const yieldMutation = useMutation({
    mutationFn: async (farmId: number) => api.post(`/api/v1/analytics/farms/${farmId}/yield`),
  })

  const riskMutation = useMutation({
    mutationFn: async (farmId: number) => api.post(`/api/v1/analytics/farms/${farmId}/risks`),
  })

  const copilotMutation = useMutation({
    mutationFn: async () => api.post('/api/v1/copilot/chat', { question }),
    onSuccess: (response) => setAnswer(response.data.answer),
  })

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Farmer Dashboard</h1>
          <p className="text-sm text-slate-600">Farm overview, forecasts, weather outlook, and risk alerts.</p>
        </div>
        <Link href="/farms/new" className={"inline-flex h-10 items-center rounded-md bg-emerald-600 px-4 text-sm font-medium text-white"}>
          Add Farm
        </Link>
      </header>

      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {(farmsQuery.data ?? []).map((farm) => (
          <article key={farm.id} className="space-y-3 rounded-xl border bg-white p-4">
            <h2 className="text-lg font-medium">{farm.farm_name}</h2>
            <p className="text-sm text-slate-600">Crop: {farm.crop_type}</p>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" onClick={() => snapshotMutation.mutate(farm.id)}>
                Snapshot
              </Button>
              <Button size="sm" variant="secondary" onClick={() => yieldMutation.mutate(farm.id)}>
                Yield Forecast
              </Button>
              <Button size="sm" variant="outline" onClick={() => riskMutation.mutate(farm.id)}>
                Risk Scan
              </Button>
            </div>
          </article>
        ))}
      </section>

      <section className="rounded-xl border bg-white p-4">
        <h2 className="mb-2 text-lg font-medium">AI Copilot</h2>
        <div className="flex gap-2">
          <input
            className="w-full rounded-md border px-3 py-2"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask about weather, yield, or drought risk..."
          />
          <Button onClick={() => copilotMutation.mutate()} disabled={!question.trim()}>
            Ask
          </Button>
        </div>
        {answer ? <p className="mt-3 text-sm text-slate-700">{answer}</p> : null}
      </section>

      {farmsQuery.isError ? <p className="text-sm text-red-600">Unable to load farms. Login may be required.</p> : null}
    </main>
  )
}
