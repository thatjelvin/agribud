'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'

type Page<T> = {
  items: T[]
  total: number
  limit: number
  offset: number
}

type Farm = {
  id: string
  owner_id: string
  farm_name: string
  crop_type: string
  planting_date: string
  expected_harvest_date: string
  farm_size_ha: number
  polygon_geojson: { type: 'Polygon'; coordinates: number[][][] }
  created_at: string
}

type Snapshot = {
  id: string
  farm_id: string
  source: string
  ndvi: number
  vegetation_health_score: number
  rainfall_mm: number
  temperature_c: number
  drought_risk_score: number
  soil_moisture: number | null
  captured_at: string
}

type YieldPrediction = {
  id: string
  farm_id: string
  season: string
  predicted_yield_ton_ha: number | null
  confidence_score: number | null
  contributing_factors: Record<string, number> | null
  model_version: string
  created_at: string
}

type Risk = {
  id: string
  farm_id: string
  alert_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  recommendation: string
  resolved: boolean
  created_at: string
}

const FARMS_PAGE_SIZE = 50

function severityClass(severity: Risk['severity']): string {
  switch (severity) {
    case 'critical':
      return 'bg-red-100 text-red-800 border-red-300'
    case 'high':
      return 'bg-orange-100 text-orange-800 border-orange-300'
    case 'medium':
      return 'bg-amber-100 text-amber-800 border-amber-300'
    default:
      return 'bg-slate-100 text-slate-800 border-slate-300'
  }
}

export default function FarmerDashboardPage() {
  const queryClient = useQueryClient()
  const [selectedFarmId, setSelectedFarmId] = useState<string | null>(null)
  const [question, setQuestion] = useState('')
  const [copilotAnswer, setCopilotAnswer] = useState<string | null>(null)
  const [copilotSources, setCopilotSources] = useState<string[] | null>(null)

  const farmsQuery = useQuery({
    queryKey: ['farms', FARMS_PAGE_SIZE, 0],
    queryFn: async () => {
      const response = await api.get<Page<Farm>>(
        `/api/v1/farms?limit=${FARMS_PAGE_SIZE}&offset=0`
      )
      return response.data
    },
  })

  const allFarms = farmsQuery.data?.items ?? []
  const farmsTotal = farmsQuery.data?.total ?? 0
  const farmsLimit = farmsQuery.data?.limit ?? FARMS_PAGE_SIZE
  const farmsOffset = farmsQuery.data?.offset ?? 0
  const canLoadMoreFarms = farmsOffset + farmsLimit < farmsTotal

  const snapshotsQuery = useQuery({
    queryKey: ['snapshots', selectedFarmId],
    queryFn: async () => {
      if (!selectedFarmId) return { items: [] as Snapshot[], total: 0, limit: 0, offset: 0 }
      const response = await api.get<Page<Snapshot>>(
        `/api/v1/analytics/farms/${selectedFarmId}/snapshots?limit=10&offset=0`
      )
      return response.data
    },
    enabled: !!selectedFarmId,
  })

  const yieldsQuery = useQuery({
    queryKey: ['yields', selectedFarmId],
    queryFn: async () => {
      if (!selectedFarmId) return { items: [] as YieldPrediction[], total: 0, limit: 0, offset: 0 }
      const response = await api.get<Page<YieldPrediction>>(
        `/api/v1/analytics/farms/${selectedFarmId}/yields?limit=10&offset=0`
      )
      return response.data
    },
    enabled: !!selectedFarmId,
  })

  const risksQuery = useQuery({
    queryKey: ['risks', selectedFarmId],
    queryFn: async () => {
      if (!selectedFarmId) return { items: [] as Risk[], total: 0, limit: 0, offset: 0 }
      const response = await api.get<Page<Risk>>(
        `/api/v1/analytics/farms/${selectedFarmId}/risks?limit=50&offset=0`
      )
      return response.data
    },
    enabled: !!selectedFarmId,
  })

  const snapshotMutation = useMutation({
    mutationFn: async (farmId: string) =>
      api.post<Snapshot>(`/api/v1/analytics/farms/${farmId}/snapshot`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['snapshots', selectedFarmId] })
      queryClient.invalidateQueries({ queryKey: ['risks', selectedFarmId] })
    },
  })

  const yieldMutation = useMutation({
    mutationFn: async (farmId: string) =>
      api.post<YieldPrediction>(`/api/v1/analytics/farms/${farmId}/yield`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['yields', selectedFarmId] })
    },
  })

  const copilotMutation = useMutation({
    mutationFn: async () =>
      api.post<{ reply: string; sources: string[] | null }>(
        '/api/v1/copilot/chat',
        { message: question, farm_id: selectedFarmId }
      ),
    onSuccess: (response) => {
      setCopilotAnswer(response.data.reply)
      setCopilotSources(response.data.sources ?? null)
    },
  })

  const farms = allFarms
  const selectedFarm = farms.find((f) => f.id === selectedFarmId) ?? null
  const latestSnapshot = snapshotsQuery.data?.items?.[0] ?? null
  const latestYield = yieldsQuery.data?.items?.[0] ?? null
  const openRisks = (risksQuery.data?.items ?? []).filter((r) => !r.resolved)

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Farmer Dashboard</h1>
          <p className="text-sm text-slate-600">
            Farm overview, forecasts, weather outlook, and risk alerts.
          </p>
        </div>
        <Link
          href="/farms/new"
          className="inline-flex h-10 items-center rounded-md bg-emerald-600 px-4 text-sm font-medium text-white"
        >
          Add Farm
        </Link>
      </header>

      <section className="space-y-3">
        <div className="flex items-center justify-between text-sm text-slate-600">
          <span>
            Showing {farms.length} of {farmsTotal} farms
          </span>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {farms.map((farm) => (
            <article
              key={farm.id}
              className={`space-y-3 rounded-xl border bg-white p-4 ${
                selectedFarmId === farm.id ? 'ring-2 ring-emerald-500' : ''
              }`}
            >
              <h2 className="text-lg font-medium">{farm.farm_name}</h2>
              <p className="text-sm text-slate-600">Crop: {farm.crop_type}</p>
              <p className="text-xs text-slate-500">
                Planted {farm.planting_date} • Harvest {farm.expected_harvest_date} •{' '}
                {farm.farm_size_ha} ha
              </p>
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  onClick={() => {
                    setSelectedFarmId(farm.id)
                    snapshotMutation.mutate(farm.id)
                  }}
                  disabled={snapshotMutation.isPending}
                >
                  Snapshot
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    setSelectedFarmId(farm.id)
                    yieldMutation.mutate(farm.id)
                  }}
                  disabled={yieldMutation.isPending}
                >
                  Yield Forecast
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setSelectedFarmId(farm.id)}
                >
                  Inspect
                </Button>
              </div>
            </article>
          ))}
        </div>
        {canLoadMoreFarms ? (
          <p className="text-xs text-slate-500">
            {farmsTotal - farms.length} more farms available. Increase the
            `limit` query param (up to 200) to load additional pages.
          </p>
        ) : null}
      </section>

      {selectedFarm ? (
        <>
          <section className="rounded-xl border bg-white p-4">
            <h2 className="mb-2 text-lg font-medium">Latest snapshot</h2>
            {latestSnapshot ? (
              <dl className="grid grid-cols-2 gap-2 text-sm md:grid-cols-5">
                <div>
                  <dt className="text-slate-500">NDVI</dt>
                  <dd className="font-mono">{latestSnapshot.ndvi.toFixed(2)}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Health</dt>
                  <dd className="font-mono">
                    {latestSnapshot.vegetation_health_score.toFixed(1)}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500">Rain</dt>
                  <dd className="font-mono">{latestSnapshot.rainfall_mm.toFixed(1)} mm</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Temp</dt>
                  <dd className="font-mono">{latestSnapshot.temperature_c.toFixed(1)} °C</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Drought risk</dt>
                  <dd className="font-mono">
                    {latestSnapshot.drought_risk_score.toFixed(2)}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="text-sm text-slate-500">
                No snapshots yet. Click "Snapshot" to capture one.
              </p>
            )}
          </section>

          <section className="rounded-xl border bg-white p-4">
            <h2 className="mb-2 text-lg font-medium">Latest yield prediction</h2>
            {latestYield && latestYield.predicted_yield_ton_ha != null ? (
              <div className="space-y-1 text-sm">
                <p>
                  <span className="text-slate-500">Predicted:</span>{' '}
                  <span className="font-mono">
                    {latestYield.predicted_yield_ton_ha.toFixed(2)} t/ha
                  </span>{' '}
                  <span className="text-slate-500">
                    (confidence {((latestYield.confidence_score ?? 0) * 100).toFixed(0)}%)
                  </span>
                </p>
                <p className="text-xs text-slate-500">
                  Model: {latestYield.model_version} • Season: {latestYield.season}
                </p>
              </div>
            ) : (
              <p className="text-sm text-slate-500">
                No prediction yet. Capture a snapshot first, then click "Yield Forecast".
              </p>
            )}
          </section>

          <section className="rounded-xl border bg-white p-4">
            <h2 className="mb-2 text-lg font-medium">Open risks</h2>
            {openRisks.length === 0 ? (
              <p className="text-sm text-slate-500">No open risks.</p>
            ) : (
              <ul className="space-y-2">
                {openRisks.map((risk) => (
                  <li
                    key={risk.id}
                    className={`rounded-md border p-3 text-sm ${severityClass(risk.severity)}`}
                  >
                    <div className="flex items-center justify-between">
                      <strong className="capitalize">
                        {risk.alert_type.replace(/_/g, ' ')}
                      </strong>
                      <span className="text-xs uppercase tracking-wide">
                        {risk.severity}
                      </span>
                    </div>
                    <p className="mt-1">{risk.message}</p>
                    <p className="mt-1 text-xs italic">{risk.recommendation}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      ) : null}

      <section className="rounded-xl border bg-white p-4">
        <h2 className="mb-2 text-lg font-medium">AI Copilot</h2>
        <div className="flex gap-2">
          <input
            className="w-full rounded-md border px-3 py-2"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder={
              selectedFarm
                ? `Ask about ${selectedFarm.farm_name}...`
                : 'Select a farm first to ground the question in your data.'
            }
            disabled={!selectedFarm}
          />
          <Button
            onClick={() => copilotMutation.mutate()}
            disabled={!question.trim() || !selectedFarm || copilotMutation.isPending}
          >
            Ask
          </Button>
        </div>
        {copilotAnswer ? (
          <div className="mt-3 space-y-1 text-sm text-slate-700">
            <p>{copilotAnswer}</p>
            {copilotSources && copilotSources.length > 0 ? (
              <p className="text-xs text-slate-500">Sources: {copilotSources.join(' • ')}</p>
            ) : null}
          </div>
        ) : null}
      </section>

      {farmsQuery.isError ? (
        <p className="text-sm text-red-600">Unable to load farms. Login may be required.</p>
      ) : null}
    </main>
  )
}
