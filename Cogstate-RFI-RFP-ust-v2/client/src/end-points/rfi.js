import axios from "../utils/axios-interceptor";

// API to fetch active RFI list
export const activeRFIListApi = async () => {
  try {
    const res = await axios.get(`/activeRFIList`);
    if (!res?.data) {
      throw new Error('No data received from server');
    }
    return res.data.data;
  } catch (error) {
    console.error('Error fetching active RFI list:', error);
    throw error; // Re-throw error for handling by caller
  }
};

// API to fetch RFI details by ID
export const getRFIDetailsApi = async (responseId) => {
  try {
    const res = await axios.get(`/response/?id=${responseId}`);
    if (!res?.data) {
      throw new Error('No data received from server');
    }
    return res.data;
  } catch (error) {
    console.error('Error fetching RFI details:', error);
    throw error; // Re-throw error for handling by caller
  }
};