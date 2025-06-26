import React, { useState, useEffect } from 'react'
import { schedule_email, response } from '../services/email'

interface CategoryTimer {
  category: string
  hour: string
  minute: string
  folderName: string
  countdown: number  // seconds left
  active: boolean
}

const initialCategories: CategoryTimer[] = [
  'Billing Issues',
  'Technical Support',
  'Account Management',
  'Claims & Disputes',
  'General Inquiry',
  'Medical Inquiry',
].map((c) => ({
  category: c,
  hour: '',
  minute: '',
  folderName: '',
  countdown: 0,
  active: false,
}))

export const ScheduleResponsePage: React.FC = () => {
  const [cats, setCats] = useState<CategoryTimer[]>(initialCategories)
  // 1. Tick every second, decrementing countdowns and firing response(...)
  useEffect(() => {
    const iv = setInterval(() => {
      setCats((prev) =>
        prev.map((c) => {
          if (!c.active || c.countdown <= 0) return c
          const next = c.countdown - 1
          if (next <= 0) {
            triggerSchedule(c)
            return { ...c, countdown: 0, active: false }
          }
          return { ...c, countdown: next }
        })
      )
    }, 1000)
    return () => clearInterval(iv)
  }, []);

  // 2. When countdown hits zero, call your response service
  const triggerSchedule = async (c: CategoryTimer) => {
    try {
      const result = await response({
        category: c.category,
        folder: c.folderName,
      })
      console.log(`Response sent for ${c.category}:, result`)
    } catch (err) {
      console.error('Error sending response:', err)
    }
  }

  // 3. User clicks “Schedule”: validate, compute diff, start countdown + persist via schedule_email
  const startTimer = (idx: number) => {
    setCats((prev) => {
      const c = prev[idx]
      const h = parseInt(c.hour, 10)
      const m = parseInt(c.minute, 10)

      // validation
      if (
        isNaN(h) ||
        isNaN(m) ||
        h < 0 ||
        h > 23 ||
        m < 0 ||
        m > 59 ||
        !c.folderName.trim()
      ) {
        alert('Please enter valid hour (0–23), minute (0–59) and folder name.')
        return prev
      }

      // compute seconds until next occurrence
      const now = new Date()
      let target = new Date()
      target.setHours(h, m, 0, 0)
      if (target.getTime() <= now.getTime()) {
        target = new Date(target.getTime() + 24 * 3600 * 1000)
      }
      const diff = Math.floor((target.getTime() - now.getTime()) / 1000)

      // persist on backend
      schedule_email({
        category: c.category,
        hour: c.hour,
        minute: c.minute,
        folderName: c.folderName,
      })
        .then((sched) => console.log('Scheduled on server:', sched))
        .catch((err) => console.error('Schedule failed:', err))

      // start local countdown
      const updated = [...prev]
      updated[idx] = { ...c, countdown: diff, active: true }
      return updated
    })
  }

  // helper to format HH:MM:SS
  const formatTime = (secs: number) => {
    const h = Math.floor(secs / 3600)
    const m = Math.floor((secs % 3600) / 60)
    const s = secs % 60
    const pad = (n: number) => n.toString().padStart(2, '0')
    return `${pad(h)}:${pad(m)}:${pad(s)}`
  }

  // update inputs
  const updateField = (
    idx: number,
    field: 'hour' | 'minute' | 'folderName',
    value: string
  ) => {
    setCats((prev) => {
      const updated = [...prev]
      updated[idx] = { ...updated[idx], [field]: value }
      return updated
    })
  }

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-white">
      <h1 className="text-3xl mb-6">Schedule Responses</h1>
      <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        {cats.map((c, i) => (
          <div
            key={c.category}
            className="bg-gray-800 rounded-lg shadow p-4 flex flex-col"
          >
            <h2 className="text-xl font-semibold mb-2">{c.category}</h2>
            <div className="flex space-x-2 mb-2">
              <input
                type="number"
                min={0}
                max={23}
                placeholder="HH"
                className="w-16 p-1 rounded bg-gray-700 text-white"
                value={c.hour}
                onChange={(e) => updateField(i, 'hour', e.target.value)}
                disabled={c.active}
              />
              <span className="self-center">:</span>
              <input
                type="number"
                min={0}
                max={59}
                placeholder="MM"
                className="w-16 p-1 rounded bg-gray-700 text-white"
                value={c.minute}
                onChange={(e) => updateField(i, 'minute', e.target.value)}
                disabled={c.active}
              />
            </div>
            <input
              type="text"
              placeholder="Folder Name"
              className="p-1 rounded bg-gray-700 text-white mb-4"
              value={c.folderName}
              onChange={(e) => updateField(i, 'folderName', e.target.value)}
              disabled={c.active}
            />

            {c.active ? (
              <div className="mt-auto text-center text-lg font-mono">
                ⏳ {formatTime(c.countdown)}
              </div>
            ) : (
              <button
                className="mt-auto bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
                onClick={() => startTimer(i)}
              >
                Schedule
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default ScheduleResponsePage