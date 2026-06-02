'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useRouter } from 'next/navigation'

import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'

const MIN_PASSWORD_LENGTH = 8

type RegisterError = {
  detail?: string
  code?: string
  errors?: Array<{ loc?: Array<string | number>; msg?: string }>
} | undefined

function firstServerError(data: RegisterError | undefined): string | null {
  if (!data) return null
  if (data.errors && data.errors.length > 0) {
    const first = data.errors[0]
    if (first?.msg) {
      const cleaned = first.msg.replace(/^Value error,\s*/i, '')
      return cleaned
    }
  }
  return data.detail ?? null
}

export default function RegisterPage() {
  const router = useRouter()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const validate = (): string | null => {
    if (!name.trim()) return 'Name is required.'
    if (!email.trim()) return 'Email is required.'
    if (password.length < MIN_PASSWORD_LENGTH) {
      return `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`
    }
    if (password !== confirm) return 'Passwords do not match.'
    return null
  }

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }
    setSubmitting(true)
    try {
      const response = await api.post('/api/v1/auth/register', {
        email: email.trim(),
        password,
        name: name.trim(),
      })
      const accessToken = response.data?.access_token
      if (typeof accessToken === 'string' && accessToken.length > 0) {
        localStorage.setItem('access_token', accessToken)
      }
      router.push('/dashboard/farmer')
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: RegisterError } }
      const message = firstServerError(axiosError.response?.data)
      setError(message ?? 'Unable to register. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <div className="rounded-xl border bg-white p-6 shadow-sm">
        <h1 className="mb-1 text-2xl font-semibold">Create your account</h1>
        <p className="mb-4 text-sm text-slate-600">
          Start tracking your farm, forecasts, and risk alerts.
        </p>
        <form onSubmit={onSubmit} className="space-y-3">
          <input
            className="w-full rounded-md border px-3 py-2"
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Full name"
            autoComplete="name"
            required
          />
          <input
            className="w-full rounded-md border px-3 py-2"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="Email"
            autoComplete="email"
            required
          />
          <input
            className="w-full rounded-md border px-3 py-2"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Password (min 8 chars; mix letters, numbers, symbols)"
            autoComplete="new-password"
            minLength={MIN_PASSWORD_LENGTH}
            required
          />
          <input
            className="w-full rounded-md border px-3 py-2"
            type="password"
            value={confirm}
            onChange={(event) => setConfirm(event.target.value)}
            placeholder="Confirm password"
            autoComplete="new-password"
            minLength={MIN_PASSWORD_LENGTH}
            required
          />
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          <Button className="w-full" type="submit" disabled={submitting}>
            {submitting ? 'Creating account…' : 'Create account'}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-600">
          Already have an account?{' '}
          <Link href="/login" className="font-medium text-emerald-700 hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  )
}
