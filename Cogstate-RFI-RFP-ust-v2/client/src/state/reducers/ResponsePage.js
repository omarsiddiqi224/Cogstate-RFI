import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { generateDraftApi, saveSectionApi, markCompleteApi, submitReviewApi, searchKnoweledgeBaseApi } from "../../end-points/ResponsePage";

const initialState = {
  loading: false,
  error: null,
  success: false,
  searchLoading: false,
  searchResults: [],
  searchError: null
};

export const generateDraft = createAsyncThunk(
  "response/generateDraft",
  async (payload, thunkAPI) => {
    try {
      const response = await generateDraftApi(payload);
      return response;
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error.response?.data || "Failed to generate draft"
      );
    }
  }
);

export const saveSection = createAsyncThunk(
  "response/saveSection",
  async (payload, thunkAPI) => {
    try {
      const response = await saveSectionApi(payload);
      return response;
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error.response?.data || "Failed to save section"
      );
    }
  }
);

export const markComplete = createAsyncThunk(
  "response/markComplete",
  async (payload, thunkAPI) => {
    try {
      const response = await markCompleteApi(payload);
      return response;
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error.response?.data || "Failed to mark complete"
      );
    }
  }
);

export const submitReview = createAsyncThunk(
  "response/submitReview",
  async (payload, thunkAPI) => {
    try {
      const response = await submitReviewApi(payload);
      return response;
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error.response?.data || "Failed to submit review"
      );
    }
  }
);

export const searchKnoweledgeBase = createAsyncThunk(
  "response/searchKnoweledgeBase",
  async (payload, thunkAPI) => {
    try {
      const response = await searchKnoweledgeBaseApi(payload);
      return response;
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error.response?.data || "Failed to search knowledge base"
      );
    }
  }
);

const responseSlice = createSlice({
  name: "response",
  initialState,
  reducers: {
    clearSearchResults: (state) => {
      state.searchResults = [];
      state.searchError = null;
    },
    clearErrors: (state) => {
      state.error = null;
      state.searchError = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // Generate Draft
      .addCase(generateDraft.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(generateDraft.fulfilled, (state, action) => {
        state.loading = false;
        state.success = true;
        state.error = null;
      })
      .addCase(generateDraft.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "An error occurred";
        state.success = false;
      })

      // Save Section
      .addCase(saveSection.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(saveSection.fulfilled, (state) => {
        state.loading = false;
        state.success = true;
        state.error = null;
      })
      .addCase(saveSection.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Failed to save section";
      })

      // Mark Complete
      .addCase(markComplete.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(markComplete.fulfilled, (state) => {
        state.loading = false;
        state.success = true;
        state.error = null;
      })
      .addCase(markComplete.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Failed to mark complete";
      })

      // Submit Review
      .addCase(submitReview.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(submitReview.fulfilled, (state) => {
        state.loading = false;
        state.success = true;
        state.error = null;
      })
      .addCase(submitReview.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Failed to submit review";
      })
      
      // Search Knowledge Base
      .addCase(searchKnoweledgeBase.pending, (state) => {
        state.searchLoading = true;
        state.searchError = null;
      })
      .addCase(searchKnoweledgeBase.fulfilled, (state, action) => {
        state.searchLoading = false;
        state.searchResults = action.payload.data || action.payload;
        state.searchError = null;
      })
      .addCase(searchKnoweledgeBase.rejected, (state, action) => {
        state.searchLoading = false;
        state.searchError = action.payload || "Failed to search knowledge base";
        state.searchResults = [];
      });
  },
});

export const { clearSearchResults, clearErrors } = responseSlice.actions;
export default responseSlice.reducer;