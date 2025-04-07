/*
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getEmails, Email } from "../services/email";

export const useEmails = () => {
  return useQuery({
    queryKey: ["emails"],
    queryFn: getEmails,
  });
};

export const useApprove = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Email }) =>
      approveEmail(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
    },
  });
};


export const useStudent = (id: number) => {
  return useQuery({
    queryKey: ['student', id],
    queryFn: () => getStudent(id)
  });
};

export const useDeleteStudent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteStudent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
    },
  });
};
*/
