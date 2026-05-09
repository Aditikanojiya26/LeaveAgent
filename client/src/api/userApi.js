import api from "./axios";

export const fetchManagers = async () => {
  const res = await api.get("/users/managers");
  console.log(res.data)
  return res.data;
};

