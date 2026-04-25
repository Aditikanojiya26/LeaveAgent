import api from "./axios";

export const createChat = async () => {
  const res = await api.post("/chats");
  return res.data;
};

export const getChats = async () => {
  const res = await api.get("/chats");
  return res.data;
};

export const sendMessage = async ({ chatId, message }) => {
  const res = await api.post(`/chats/${chatId}/message`, { message });
  return res.data;
};
export const getChatMessages = async (chatId) => {
  const res = await api.get(`/chats/${chatId}/messages`);
  return res.data;
};