import axios from "../utils/axios-interceptor";

export const generateDraftApi = async(payload) => {
  try {
    const res = await axios.post(`/generateDraft`, payload);
    return res.data;
  } catch (error) {
    throw error;
  }
};

export const saveSectionApi = async(payload) => {
  try {
    const res = await axios.post(`/saveSection`, payload);
    return res.data;
  } catch (error) {
    throw error;
  }
};

export const markCompleteApi = async(payload) => {
  try {
    const res = await axios.post(`/markComplete`, payload);
    return res.data;
  } catch (error) {
    throw error;
  }
};

export const submitReviewApi = async(payload) => {
  try {
    const res = await axios.post(`/submitReview`, payload);
    return res.data;
  } catch (error) {
    throw error;
  }
};

export const searchKnoweledgeBaseApi = async(payload) => {
  try {
    const res = await axios.post(`/searchKnowledgeBase`, payload);
    return res.data;
  } catch (error) {
    throw error;
  }
};

export const exportRFIApi = async(responseId) => {
  try {
    const res = await axios.get(`/exportRFI/${responseId}`);
    return res.data;
  } catch (error) {
    throw error;
  }
};