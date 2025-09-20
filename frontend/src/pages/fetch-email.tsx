import { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Checkbox,
  FormControlLabel,
  TextField,
} from '@mui/material';
import {
  getEmails,
  deleteEmail,
  approveEmail,
  editAiResponse,
  rejectEmails as apiRejectEmails,
  flagEmails as apiFlagEmails,
  approveByCategory as apiApproveByCategory,
  approveBatch as apiApproveBatch,
} from '../services/email';

// ---- Types ----
export interface AIResponse {
  to?: string | null;
  subject?: string | null;
  body?: string | null;
  error?: string | null;
}

export interface Email {
  id: string;
  subject: string;
  body: string;
  sender: string;
  category: string;
  date: string;
  status: string;
  ai_response: AIResponse;
}

// ---- Helpers ----
function normalizeAiResp(raw: unknown): AIResponse {
  if (raw && typeof raw === 'object') {
    const r = raw as Record<string, unknown>;
    return {
      to: (r.to as string) ?? null,
      subject: (r.subject as string) ?? null,
      body: (r.body as string) ?? (r.response as string) ?? null, // support legacy {response}
      error: (r.error as string) ?? null,
    };
  }
  if (typeof raw === 'string') {
    // legacy plain text or "Pending"
    return { body: raw };
  }
  return { body: 'PENDING' };
}

function EmailPage() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const [selectedEmailIds, setSelectedEmailIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [approveCategory, setApproveCategory] = useState('');

  // Edit AI Response
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editResponseText, setEditResponseText] = useState('');
  const [editingEmailId, setEditingEmailId] = useState<string | null>(null);

  useEffect(() => {
    fetchEmails();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchEmails = async () => {
    try {
      const resp = await getEmails();
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const formatted: Email[] = resp.map((e: any) => ({
        id: e.id,
        subject: e.subject,
        body: e.body?.content ?? '',
        sender: e.sender?.emailAddress?.name ?? e.sender?.emailAddress?.address ?? 'Unknown',
        category: typeof e.category === 'object' ? e.category.category : e.category,
        date: new Date(e.receivedDateTime).toLocaleDateString(),
        status: e.status,
        ai_response: normalizeAiResp(e.ai_response || 'PENDING'),
      }));
      setEmails(formatted);
    } catch (err) {
      console.error(err);
    }
  };

  const handleEditClick = (email: Email) => {
    setEditResponseText(email.ai_response.body || '');
    setEditingEmailId(email.id);
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!editingEmailId) return;
    try {
      // Backend accepts either string (body only) or object
      const res = await editAiResponse(editingEmailId, editResponseText);
      const newAi = normalizeAiResp(res?.ai_response ?? { body: editResponseText });

      setEmails(prev =>
        prev.map(e =>
          e.id === editingEmailId ? { ...e, ai_response: newAi, status: res?.status ?? e.status } : e
        )
      );
      setEditDialogOpen(false);
      setEditingEmailId(null);
      setEditResponseText('');
    } catch (err) {
      console.error('Failed to update AI response:', err);
    }
  };

  const handleDelete = async (id: string) => {
    await deleteEmail(id);
    setEmails(prev => prev.filter(e => e.id !== id));
    setSelectedEmailIds(prev => prev.filter(x => x !== id));
  };

  const handleApprove = async (id: string) => {
    const resp = await approveEmail(id);
    setEmails(prev => prev.map(e => (e.id === id ? { ...e, status: resp.status } : e)));
  };

  const handleReject = async () => {
    if (!selectedEmailIds.length) return;
    setLoading(true);
    await apiRejectEmails(selectedEmailIds);
    await fetchEmails();
    setSelectedEmailIds([]);
    setLoading(false);
  };

  const handleFlag = async () => {
    if (!selectedEmailIds.length) return;
    setLoading(true);
    await apiFlagEmails(selectedEmailIds);
    await fetchEmails();
    setSelectedEmailIds([]);
    setLoading(false);
  };

  const handleApproveSelected = async () => {
    if (!selectedEmailIds.length) return;
    setLoading(true);
    await apiApproveBatch(selectedEmailIds);
    await fetchEmails();
    setSelectedEmailIds([]);
    setLoading(false);
  };

  const handleApproveCategory = async () => {
    if (!approveCategory) return;
    setLoading(true);
    await apiApproveByCategory(approveCategory);
    await fetchEmails();
    setApproveCategory('');
    setLoading(false);
  };

  const handleCheckboxChange = (id: string) => {
    setSelectedEmailIds(prev => (prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]));
  };

  const handleSelectAll = (checked: boolean) => {
    setSelectedEmailIds(checked ? emails.map(e => e.id) : []);
  };

  const isAllSelected = emails.length > 0 && selectedEmailIds.length === emails.length;
  const truncate = (text: string, n: number) => (text && text.length > n ? text.slice(0, n) + '…' : text || '');

  return (
    <div style={{ padding: 16 }}>
      <Typography variant="h4" color="white" gutterBottom>
        Email List
      </Typography>

      {/* Bulk Actions */}
      <div style={{ marginBottom: 16 }}>
        <FormControlLabel
          control={
            <Checkbox
              checked={isAllSelected}
              onChange={e => handleSelectAll(e.target.checked)}
              sx={{ color: 'white' }}
            />
          }
          label="Select All"
        />
        <Button
          variant="contained"
          color="primary"
          onClick={handleApproveSelected}
          disabled={loading || !selectedEmailIds.length}
          sx={{ mr: 1 }}
        >
          Approve Selected
        </Button>
        <Button
          variant="contained"
          color="error"
          onClick={handleReject}
          disabled={loading || !selectedEmailIds.length}
          sx={{ mr: 1 }}
        >
          Reject Selected
        </Button>
        <Button
          variant="contained"
          onClick={handleFlag}
          disabled={loading || !selectedEmailIds.length}
          sx={{ mr: 1 }}
        >
          Flag Selected
        </Button>
        <TextField
          placeholder="Category"
          value={approveCategory}
          onChange={e => setApproveCategory(e.target.value)}
          size="small"
          sx={{ ml: 2, bgcolor: 'white', borderRadius: 1 }}
        />
        <Button
          variant="contained"
          onClick={handleApproveCategory}
          disabled={loading || !approveCategory}
          sx={{ ml: 1 }}
        >
          Approve by Category
        </Button>
      </div>

      {/* Email Cards */}
      <Grid container spacing={3}>
        {emails.map(email => (
          <Grid key={email.id}>
            <Card sx={{ bgcolor: '#333', color: 'white', height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={selectedEmailIds.includes(email.id)}
                      onChange={() => handleCheckboxChange(email.id)}
                      sx={{ color: 'white' }}
                    />
                  }
                  label="Select"
                />
                <Typography variant="h6">{truncate(email.subject, 80)}</Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {truncate(email.body, 200)}
                </Typography>

                <Typography variant="subtitle2" color="gray">
                  From: {email.sender}
                </Typography>
                <Typography variant="subtitle2" color="gray">
                  Category: {email.category}
                </Typography>

                {/* AI Summary */}
                {email.ai_response.error ? (
                  <Typography variant="subtitle2" color="error">
                    AI Error: {email.ai_response.error}
                  </Typography>
                ) : (
                  <>
                    {email.ai_response.subject && (
                      <Typography variant="subtitle2" color="gray">
                        AI Subject: {truncate(email.ai_response.subject, 80)}
                      </Typography>
                    )}
                    {email.ai_response.to && (
                      <Typography variant="subtitle2" color="gray">
                        AI To: {email.ai_response.to}
                      </Typography>
                    )}
                    {email.ai_response.body ? (
                      <Typography variant="body2" color="gray" sx={{ whiteSpace: 'pre-wrap' }}>
                        {truncate(email.ai_response.body, 200)}
                      </Typography>
                    ) : (
                      <Typography variant="subtitle2" color="gray">AI: PENDING</Typography>
                    )}
                  </>
                )}

                <Typography variant="subtitle2" color="gray">
                  Date: {email.date}
                </Typography>
                <Typography variant="subtitle2" color="gray">
                  Status: {email.status}
                </Typography>
              </CardContent>
              <CardActions>
                <Button size="small" onClick={() => setSelectedEmail(email)} sx={{ color: 'white' }}>
                  Details
                </Button>
                <Button size="small" onClick={() => handleDelete(email.id)} sx={{ color: 'white' }}>
                  Delete
                </Button>
                <Button size="small" onClick={() => handleApprove(email.id)} sx={{ color: 'white' }}>
                  Approve
                </Button>
                <Button size="small" onClick={() => handleEditClick(email)} sx={{ color: 'white' }}>
                  Edit AI
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Email Details Dialog */}
      <Dialog open={!!selectedEmail} onClose={() => setSelectedEmail(null)} fullWidth maxWidth="md">
        <DialogTitle>Email Details</DialogTitle>
        <DialogContent dividers>
          {selectedEmail && (
            <>
              <Typography variant="h6" gutterBottom>{selectedEmail.subject}</Typography>
              <Typography paragraph sx={{ whiteSpace: 'pre-wrap' }}>{selectedEmail.body}</Typography>

              <Typography variant="body2" gutterBottom>From: {selectedEmail.sender}</Typography>
              <Typography variant="body2" gutterBottom>Category: {selectedEmail.category}</Typography>

              <Typography variant="subtitle1" gutterBottom>AI RESPONSE</Typography>
              <Typography variant="body2" gutterBottom><strong>AI To:</strong> {selectedEmail.ai_response.to || selectedEmail.sender || '—'}</Typography>
              <Typography variant="body2" gutterBottom><strong>AI Subject:</strong> {selectedEmail.ai_response.subject || selectedEmail.subject || '—'}</Typography>

              {selectedEmail.ai_response.error ? (
                <Typography variant="body2" color="error"><strong>Error:</strong> {selectedEmail.ai_response.error}</Typography>
              ) : (
                <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                  <strong>AI RESPONSE: </strong> {selectedEmail.ai_response.body || 'PENDING'}
                </Typography>
              )}

              <Typography variant="body2" gutterBottom>Date: {selectedEmail.date}</Typography>
              <Typography variant="body2" gutterBottom>Status: {selectedEmail.status}</Typography>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedEmail(null)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Edit AI Response Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Edit AI Response</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={6}
            value={editResponseText}
            onChange={e => setEditResponseText(e.target.value)}
            placeholder="Edit AI-generated email body..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveEdit}>Save</Button>
        </DialogActions>
      </Dialog>
    </div>
  );
}

export default EmailPage;
