import axios from "../utils/axios-interceptor";

export const getAuditTrailApi = async(payload) => {
  try {
    const res = await axios.get(`/auditTrail?id=${payload.id}`);
    return res.data;
  } catch (error) {
    throw error;
  }
};