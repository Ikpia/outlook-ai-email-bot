import api from "./email-api-client";

export interface Email {
  id: string;
  subject: string;
  body: string;
  sender: string;
  category: { category: string } | string;
  date: string;
  ai_response: string;
}

export interface Schedule {
  category: string;
  hour: string;
  minute: string;
  folderName: string;
}

export interface Respond {
  category: string;
}

export const getEmails = async () => {
  //const response = await api(`/fetch-outlook-emails`);
  //console.log(response);
  //if (response.status == 200) {
  const emails = await api(`/get-emails`);
  const { data } = emails;
  return data;
  //}
  //return [];
};

/*
export const approveEmail = async (
  id: number,
  student: Email
): Promise<Email> => {
  const response = await apiClient.put(`/students/${id}`, student);
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
