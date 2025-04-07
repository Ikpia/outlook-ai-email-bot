/*
import { Card, CardContent, CardActions, Typography, Button, Grid } from '@mui/material';
import rawData from './email.json';

export interface Email {
  id: string;
  subject: string;
  body: string;
  sender: string;
  category: string;
  date: string;
  status: string;
}

const ai_response: string = "Pending";

function EmailPage() {
  // Process raw data to match the Email interface
  const emails: Email[] = rawData.map((email) => ({
    id: email.id,
    subject: email.subject,
    body: email.body.content,
    sender: email.sender.emailAddress.name,
    category:
      typeof email.category === 'object'
        ? email.category.category
        : email.category,
    date: new Date(email.receivedDateTime).toLocaleDateString(),
    status: email.status
  }));

  // Function to truncate text to a specified length
  const truncateText = (text: string, maxLength: number) => {
    return text.length > maxLength
      ? `${text.substring(0, maxLength)}...`
      : text;
  };

  return (
    <div style={{ padding: '16px' }}>
      <Typography variant="h4" gutterBottom style={{ color: 'white' }}>
        Email List
      </Typography>
      <Grid container spacing={3}>
        {emails.map((email) => (
          <Grid key={email.id}>
            <Card sx={{ backgroundColor: '#333', color: 'white' }}>
              <CardContent>
                <Typography variant="h6">
                  {truncateText(email.subject, 50)}
                </Typography>
                <Typography variant="body2">
                  {truncateText(email.body, 200)}
                </Typography>
                <Typography variant="subtitle2" color="gray">
                  From: {email.sender}
                </Typography>
                <Typography variant="subtitle2" color="gray">
                  Category: {email.category}
                </Typography>
                <Typography variant="subtitle2" color="gray">
                  AI RESPONSE: {ai_response}
                </Typography>
                <Typography variant="subtitle2" color="gray">
                  Date: {email.date}
                </Typography>
                <Typography variant="subtitle2" color="gray">
                  STATUS: {email.status}
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  sx={{ color: 'white' }}
                  onClick={() => alert(`Selected email ID: ${email.id}`)}
                >
                  Select
                </Button>
                <Button
                  size="small"
                  sx={{ color: 'white' }}
                  onClick={() => alert(`Selected email ID: ${email.id}`)}
                >
                  Delete
                </Button>
                <Button
                  size="small"
                  sx={{ color: 'white' }}
                  onClick={() => alert(`Update email ID: ${email.id}`)}
                >
                  Approve
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </div>
  );
}

export default EmailPage;
*/




// EmailPage.tsx
import { useState, useEffect } from 'react'
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Grid,
} from '@mui/material'
//import rawData from './email.json'
import {getEmails, deleteEmail } from '../services/email'

// 1. Extend interface to include ai_response
export interface Email {
  id: string
  subject: string
  body: string
  sender: string
  category: string
  date: string
  status: string
  ai_response: string
}

function EmailPage() {
  // 2. Initialize state from rawData, pulling ai_response if present
  const [emails, setEmails] = useState<Email[]>([]);

  useEffect(() => {
    const fetchEmails = async () => {
      try {
        const response = await getEmails();
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const formattedEmails = response.map((e: any) => ({
          id: e.id,
          subject: e.subject,
          body: e.body.content,
          sender: e.sender.emailAddress.name,
          category: typeof e.category === 'object' ? e.category.category : e.category,
          date: new Date(e.receivedDateTime).toLocaleDateString(),
          status: e.status,
          ai_response: e.ai_response || 'Pending',
        }));
        setEmails(formattedEmails);
      } catch (error) {
        console.error('Error fetching emails:', error);
      }
    };
  
    fetchEmails();
  }, []);
  
/*
  const [emails, setEmails] = useState<Email[]>(
    data.map((e) => ({
      id: e.id,
      subject: e.subject,
      body: e.body.content,
      sender: e.sender.emailAddress.name,
      category:
        typeof e.category === 'object' ? e.category.category : e.category,
      date: new Date(e.receivedDateTime).toLocaleDateString(),
      status: e.status,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ai_response: (e as any).ai_response || 'Pending',
    }))
  )
*/
  // 3. Truncate helper
  const truncateText = (text: string, max: number) =>
    text.length > max ? text.slice(0, max) + '…' : text

  // 4. Simulate calling your backend to “approve” and get the AI response
  const handleApprove = async (id: string) => {
    // replace with your real API call:
    const resp = await fetch(`/api/approve-email/${id}`)
    const data = await resp.json() // { ai_response: "Here's your reply…" }

    // 5. Update that one email in state
    setEmails((prev) =>
      prev.map((em) =>
        em.id === id
          ? { ...em, status: 'Responded', ai_response: data.ai_response }
          : em
      )
    )
  }

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-white">
      <Typography variant="h4" gutterBottom>
        Email List
      </Typography>
      <Grid container spacing={3}>
        {emails.map((email) => (
          <Grid key={email.id}>
            <Card sx={{ backgroundColor: '#333', color: 'white' }}>
              <CardContent>
                <Typography variant="h6">
                  {truncateText(email.subject, 50)}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  {truncateText(email.body, 200)}
                </Typography>
                <Typography variant="subtitle2" color="gray">
                  From: {email.sender}
                </Typography>
                <Typography variant="subtitle2" color="gray">
                  Category: {email.category}
                </Typography>
                <Typography variant="subtitle2" color="gray">
                  AI RESPONSE: {email.ai_response}
                </Typography>
                <Typography variant="subtitle2" color="gray">
                  Date: {email.date}
                </Typography>
                <Typography variant="subtitle2" color="gray">
                  STATUS: {email.status}
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  sx={{ color: 'white' }}
                  onClick={() => alert(`Selected email ID: ${email.id}`)}
                >
                  Select
                </Button>
                <Button
                  size="small"
                  sx={{ color: 'white' }}
                  onClick={() => deleteEmail(email.id)}
                >
                  Delete
                </Button>
                <Button
                  size="small"
                  sx={{ color: 'white' }}
                  onClick={() => handleApprove(email.id)}
                  disabled={email.status === 'Responded'}
                >
                  Approve
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </div>
  )
}

export default EmailPage
