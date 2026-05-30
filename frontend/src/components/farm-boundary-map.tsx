'use client'

import 'leaflet/dist/leaflet.css'

import { MapContainer, Marker, Polygon, TileLayer, useMapEvents } from 'react-leaflet'

type LatLngTuple = [number, number]

function ClickHandler({ onAddPoint }: { onAddPoint: (point: LatLngTuple) => void }) {
  useMapEvents({
    click(event) {
      onAddPoint([event.latlng.lat, event.latlng.lng])
    },
  })

  return null
}

export function FarmBoundaryMap({
  points,
  onChange,
}: {
  points: LatLngTuple[]
  onChange: (nextPoints: LatLngTuple[]) => void
}) {
  return (
    <div className="space-y-2">
      <MapContainer center={[6.5244, 3.3792]} zoom={6} className="h-72 w-full rounded-lg border">
        <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <ClickHandler onAddPoint={(point) => onChange([...points, point])} />
        {points.map((point, index) => (
          <Marker key={index} position={point} />
        ))}
        {points.length >= 3 ? <Polygon positions={points} /> : null}
      </MapContainer>
      <p className="text-xs text-slate-500">Click on the map to place boundary points (minimum 3).</p>
    </div>
  )
}
