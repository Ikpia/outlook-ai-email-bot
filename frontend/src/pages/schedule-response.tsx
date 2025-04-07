/*
import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
} from '@mui/material';

// Define the interface for each category timer
interface CategoryTimer {
  category: string;
  scheduleTime: number; // time in seconds that user sets
  countdown: number; // current countdown value in seconds
  isActive: boolean;
}

// Predefined categories
const initialCategories: CategoryTimer[] = [
  { category: 'Billing Issues', scheduleTime: 0, countdown: 0, isActive: false },
  { category: 'Technical Support', scheduleTime: 0, countdown: 0, isActive: false },
  { category: 'Account Management', scheduleTime: 0, countdown: 0, isActive: false },
  { category: 'Claims & Disputes', scheduleTime: 0, countdown: 0, isActive: false },
  { category: 'General Inquiry', scheduleTime: 0, countdown: 0, isActive: false },
];

const ScheduleResponsePage: React.FC = () => {
  const [categories, setCategories] = useState<CategoryTimer[]>(initialCategories);

  // Handle change in the schedule time input
  const handleTimeChange = (index: number, value: string) => {
    const newTime = parseInt(value, 10) || 0;
    setCategories((prev) => {
      const updated = [...prev];
      updated[index].scheduleTime = newTime;
      return updated;
    });
  };

  // Start the timer for a given category
  const startTimer = (index: number) => {
    setCategories((prev) => {
      const updated = [...prev];
      updated[index].countdown = updated[index].scheduleTime;
      updated[index].isActive = true;
      return updated;
    });
  };

  // useEffect to update countdown every second
  useEffect(() => {
    const interval = setInterval(() => {
      setCategories((prev) =>
        prev.map((cat) => {
          if (cat.isActive && cat.countdown > 0) {
            const newCountdown = cat.countdown - 1;
            if (newCountdown <= 0) {
              // When countdown reaches zero, trigger backend call and stop the timer.
              runScheduleResponse(cat.category);
              return { ...cat, countdown: 0, isActive: false };
            }
            return { ...cat, countdown: newCountdown };
          }
          return cat;
        })
      );
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Function to run the scheduled response (replace with your backend API call)
  const runScheduleResponse = (category: string) => {
    console.log(`Running scheduled response for ${category}`);
    // Example using fetch:
    /*
    fetch('/api/run-schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category }),
    });

  };

  return (
    <Container sx={{ padding: '16px' }}>
      <Typography variant="h4" gutterBottom sx={{ color: 'white' }}>
        Schedule Response Page
      </Typography>
      <Grid container spacing={3}>
        {categories.map((cat, index) => (
          <Grid key={cat.category}>
            <Card sx={{ backgroundColor: '#333', color: 'white' }}>
              <CardContent>
                <Typography variant="h6">{cat.category}</Typography>
                <TextField
                  label="Set Time (sec)"
                  type="number"
                  value={cat.scheduleTime}
                  onChange={(e) => handleTimeChange(index, e.target.value)}
                  fullWidth
                  InputLabelProps={{ sx: { color: 'white' } }}
                  InputProps={{ sx: { color: 'white' } }}
                  variant="outlined"
                  sx={{ marginY: 1 }}
                />
                <Typography variant="body1">
                  Countdown: {cat.countdown} sec
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  variant="contained"
                  onClick={() => startTimer(index)}
                >
                  Start
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};

export default ScheduleResponsePage;


// src/components/ScheduleResponsePage.tsx
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

const initialCategories = [
  'Billing Issues',
  'Technical Support',
  'Account Management',
  'Claims & Disputes',
  'General Inquiry',
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

  // tick every second
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
  }, [])

  const triggerSchedule = async (c: CategoryTimer) => {
    try {
      const schedule = await schedule_email({category: c.category,
        hour: c.hour,
        minute: c.minute,
        folderName: c.folderName,})
      console.log(`Scheduled response sent for ${c.category} ${schedule}`)
    } catch (err) {
      console.error(err)
    }
  }

  const startTimer = (idx: number) => {
    setCats((prev) => {
      const c = prev[idx]
      const h = parseInt(c.hour, 10)
      const m = parseInt(c.minute, 10)
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
      const now = new Date()
      let target = new Date()
      target.setHours(h, m, 0, 0)
      if (target.getTime() <= now.getTime()) {
        // schedule for next day
        target = new Date(target.getTime() + 24 * 3600 * 1000)
      }
      const diff = Math.floor((target.getTime() - now.getTime()) / 1000)
      const updated = [...prev]
      updated[idx] = { ...c, countdown: diff, active: true }
      return updated
    })
  }

  const formatTime = (secs: number) => {
    const h = Math.floor(secs / 3600)
    const m = Math.floor((secs % 3600) / 60)
    const s = secs % 60
    const pad = (n: number) => n.toString().padStart(2, '0')
    return `${pad(h)}:${pad(m)}:${pad(s)}`
  }

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
              onChange={(e) =>
                updateField(i, 'folderName', e.target.value)
              }
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
*/

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

  // 1. Tick every second, decrementing countdowns and firing `response(...)`
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
  }, [])

  // 2. When countdown hits zero, call your `response` service
  const triggerSchedule = async (c: CategoryTimer) => {
    try {
      const result = await response({
        category: c.category
      })
      console.log(`Response sent for ${c.category}:`, result)
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
