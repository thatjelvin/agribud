import Link from 'next/link'

import { buttonVariants } from '@/components/ui/button'

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col items-center justify-center gap-6 px-6 text-center">
      <h1 className="text-4xl font-semibold">AgriPulse AI MVP</h1>
      <p className="max-w-2xl text-slate-600">
        Farm intelligence platform with geospatial insights, weather risk signals, yield forecasting, and AI copilot workflows.
      </p>
      <div className="flex gap-3">
        <Link className={buttonVariants()} href="/login">
          Login
        </Link>
        <Link className={buttonVariants({ variant: 'outline' })} href="/dashboard/farmer">
          Farmer Dashboard
        </Link>
        <Link className={buttonVariants({ variant: 'secondary' })} href="/dashboard/admin">
          Admin Dashboard
        </Link>
      </div>
    </main>
  )
}
