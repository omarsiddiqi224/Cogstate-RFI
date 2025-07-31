import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { submitKnowledgeBaseEntry } from "../../end-points/knowledgeBase";

// Async thunk for submitting a knowledge base entry
export const submitKnowledgeBase = createAsyncThunk(
  'knowledgeBase/submitEntry',
  async (entryData, { rejectWithValue }) => {
    try {
      const result = await submitKnowledgeBaseEntry(entryData);
      return result;
    } catch (err) {
      console.error('Submission failed', err);
      return rejectWithValue(err.message || 'Submission failed');
    }
  }
);

const initialState = {
  isSubmitting: false,
  submitSuccess: false,
  submitError: '',
  response: null,
};

const knowledgeBase = createSlice({
  name: 'kb',
  initialState,
  reducers: {
    clearSubmissionState: (state) => {
      state.isSubmitting = false;
      state.submitSuccess = false;
      state.submitError = '';
      state.response = null;
    },
    resetForm: () => initialState, // optional, if needed elsewhere
  },
  extraReducers: (builder) => {
    builder
      .addCase(submitKnowledgeBase.pending, (state) => {
        state.isSubmitting = true;
        state.submitError = '';
        state.submitSuccess = false;
      })
      .addCase(submitKnowledgeBase.fulfilled, (state, action) => {
        state.isSubmitting = false;
        state.submitSuccess = true;
        state.submitError = '';
        state.response = action.payload;
      })
      .addCase(submitKnowledgeBase.rejected, (state, action) => {
        state.isSubmitting = false;
        state.submitSuccess = false;
        state.submitError = action.payload || 'Submission failed';
      });
  },
});

export const { clearSubmissionState, resetForm } = knowledgeBase.actions;

export default knowledgeBase.reducer;
