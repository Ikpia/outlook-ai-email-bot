import api from "./email-api-client";

export type AiEditPayload =
  | string
  | { to?: string; subject?: string; body?: string; error?: string };

export interface EditAiResponseResult {
  message: string;
  ai_response: {
    to?: string | null;
    subject?: string | null;
    body?: string | null;
    error?: string | null;
  };
  status: string;
}

export interface Email {
  id: string;
  subject: string;
  body: string;
  sender: string;
  category: { category: string } | string;
  date: string;
  ai_response: string;
  status: string;
}

export interface Schedule {
  category: string;
  hour: string;
  minute: string;
  folderName: string;
}

export interface Respond {
  category: string;
  folder: string;
  //name: string | undefined;
}

export const getEmails = async () => {
  const response = await api(`/fetch-outlook-emails`);
  console.log(response);
  if (response.status == 200) {
    const emails = await api(`/get-emails`);
    const { data } = emails;
    return data;
  }
  return [];
};

export const approveEmail = async (id: string): Promise<Email> => {
  const response = await api.post(`/approve-emails/${id}`);
  return response.data;
};

export const editAiResponse = async (
  id: string,
  ai_response: AiEditPayload,
  opts?: { status?: string; method?: 'POST' | 'PATCH' }
): Promise<EditAiResponseResult> => {
  const method = opts?.method ?? 'POST';
  const payload: Record<string, unknown> = { ai_response };
  if (opts?.status) payload.status = opts.status;

  try {
    const res = await api.request({
      url: `/edit_ai_response/${id}`,
      method,
      data: payload,
      headers: { 'Content-Type': 'application/json' },
    });
    return res.data as EditAiResponseResult;
  } catch (err: any) {
    const msg =
      err?.response?.data?.error ||
      err?.response?.data?.message ||
      err?.message ||
      'Failed to edit AI response';
    throw new Error(msg);
  }
};


/** 
export const editAiResponse = async (id: string, ai_response: string) => {
  const response = await api.post(`/edit_ai_response/${id}`, { ai_response });
  return response.data;
};
*/

export const response = async (respond: Respond) => {
  const response = await api.post(`/respond`, respond);
  return response.data;
};

export const schedule_email = async (schedule: Schedule) => {
  const response = await api.post(`/schedule-response`, schedule);
  return response.data;
};

export const deleteEmail = async (email_id: string) => {
  await api.delete(`/delete-email/${email_id}`);
};

export const rejectEmails = async (
  email_ids: string[]
): Promise<{ message: string }> => {
  const response = await api.post(`/emails/reject`, { email_ids });
  return response.data;
};

/**
 * Flag multiple emails for follow-up
 */
export const flagEmails = async (
  email_ids: string[]
): Promise<{ message: string }> => {
  const response = await api.post(`/emails/flag`, { email_ids });
  return response.data;
};

/**
 * Approve all emails within a given category
 */
export const approveByCategory = async (
  category: string
): Promise<{ approved: string[] }> => {
  const response = await api.post(`/approve-emails/by-category`, { category });
  return response.data;
};

/**
 * Approve multiple emails by IDs in batch
 */
export const approveBatch = async (
  email_ids: string[]
): Promise<{ approved: string[] }> => {
  const response = await api.post(`/approve-emails/batch`, { email_ids });
  return response.data;
};