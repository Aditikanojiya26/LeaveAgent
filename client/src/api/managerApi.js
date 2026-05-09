import api from "./axios";
export const getManagerLeaveRequests = async () => {
  const res = await api.get("/manager/leave-requests");
  return res.data;
};

export const decideLeaveRequest = async ({ leaveId, decision, reason = "" }) => {
  const res = await api.patch(
    `/manager/leave-requests/${leaveId}/decision`,
    null,
    {
      params: { decision, reason },
    }
  );

  return res.data;
};