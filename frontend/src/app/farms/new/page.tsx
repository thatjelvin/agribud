'use client'

import dynamic from 'next/dynamic'
import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'

import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'

const FarmBoundaryMap = dynamic(
  () => import('@/components/farm-boundary-map').then((module) => module.FarmBoundaryMap),
  { ssr: false }
)

export default function NewFarmPage() {
  const router = useRouter()
  const [farmName, setFarmName] = useState('Demo Farm')
  const [cropType, setCropType] = useState('Maize')
  const [plantingDate, setPlantingDate] = useState('2026-06-01')
  const [harvestDate, setHarvestDate] = useState('2026-09-01')
  const [farmSizeHa, setFarmSizeHa] = useState(2)
  const [points, setPoints] = useState<Array<[number, number]>>([])
  const [error, setError] = useState<string | null>(null)

  const polygonGeoJson = useMemo(
    () => ({
      type: 'Polygon',
      coordinates: [[...points.map(([lat, lng]) => [lng, lat]), ...(points.length > 0 ? [[points[0][1], points[0][0]]] : [])]],
    }),
    [points]
  )

  const saveFarm = async () => {
    setError(null)
    if (points.length < 3) {
      setError('Add at least 3 boundary points on the map.')
      return
    }

    try {
      await api.post('/api/v1/farms', {
        farm_name: farmName,
        crop_type: cropType,
        planting_date: plantingDate,
        expected_harvest_date: harvestDate,
        farm_size_ha: Number(farmSizeHa),
        polygon_geojson: polygonGeoJson,
      })
      router.push('/dashboard/farmer')
    } catch {
      setError('Unable to save farm. Ensure you are logged in.')
    }
  }

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-6 py-8">
      <h1 className="text-2xl font-semibold">Create Farm</h1>
      <div className="grid gap-3 md:grid-cols-2">
        <input className="rounded-md border px-3 py-2" value={farmName} onChange={(e) => setFarmName(e.target.value)} placeholder="Farm name" />
        <input className="rounded-md border px-3 py-2" value={cropType} onChange={(e) => setCropType(e.target.value)} placeholder="Crop type" />
        <input className="rounded-md border px-3 py-2" type="date" value={plantingDate} onChange={(e) => setPlantingDate(e.target.value)} />
        <input className="rounded-md border px-3 py-2" type="date" value={harvestDate} onChange={(e) => setHarvestDate(e.target.value)} />
        <input
          className="rounded-md border px-3 py-2"
          type="number"
          min={0.1}
          step={0.1}
          value={farmSizeHa}
          onChange={(e) => setFarmSizeHa(Number(e.target.value))}
          placeholder="Farm size (ha)"
        />
      </div>
      <FarmBoundaryMap points={points} onChange={setPoints} />
      <div className="rounded-md border bg-white p-3 text-sm">
        <strong>Boundary GeoJSON:</strong>
        <pre className="mt-2 overflow-auto text-xs">{JSON.stringify(polygonGeoJson, null, 2)}</pre>
      </div>
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      <div className="flex gap-2">
        <Button onClick={saveFarm}>Save Farm</Button>
        <Button variant="outline" onClick={() => setPoints([])}>
          Clear Boundary
        </Button>
      </div>
    </main>
  )
}
