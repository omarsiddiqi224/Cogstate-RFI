import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { generateDraftApi, saveSectionApi, markCompleteApi, submitReviewApi, searchKnoweledgeBaseApi, exportRFIApi } from "../../end-points/ResponsePage";

const initialState = {
  loading: false,
  error: null,
  success: false,
  searchLoading: false,
  searchResults: [],
  searchError: null,
  exportLoading: false,
  exportError: null
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
  "response/searchKnowledgeBase",
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

export const exportRFI = createAsyncThunk(
  "response/exportRFI",
  async (responseId, thunkAPI) => {
    try {
      const response = await exportRFIApi(responseId);
      return response;
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error.response?.data || "Failed to export RFI"
      );
    }
  }
);

const responseSlice = createSlice({
  name: "response",
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearSuccess: (state) => {
      state.success = false;
    },
    clearSearchResults: (state) => {
      state.searchResults = [];
      state.searchError = null;
    },
    clearExportState: (state) => {
      state.exportLoading = false;
      state.exportError = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // Generate Draft
      .addCase(generateDraft.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(generateDraft.fulfilled, (state) => {
        state.loading = false;
        state.success = true;
      })
      .addCase(generateDraft.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Save Section
      .addCase(saveSection.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(saveSection.fulfilled, (state) => {
        state.loading = false;
        state.success = true;
      })
      .addCase(saveSection.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Mark Complete
      .addCase(markComplete.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(markComplete.fulfilled, (state) => {
        state.loading = false;
        state.success = true;
      })
      .addCase(markComplete.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Submit Review
      .addCase(submitReview.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(submitReview.fulfilled, (state) => {
        state.loading = false;
        state.success = true;
      })
      .addCase(submitReview.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Search Knowledge Base
      .addCase(searchKnoweledgeBase.pending, (state) => {
        state.searchLoading = true;
        state.searchError = null;
      })
      .addCase(searchKnoweledgeBase.fulfilled, (state, action) => {
        state.searchLoading = false;
        state.searchResults = action.payload.data || [];
      })
      .addCase(searchKnoweledgeBase.rejected, (state, action) => {
        state.searchLoading = false;
        state.searchError = action.payload;
      })
      // Export RFI
      .addCase(exportRFI.pending, (state) => {
        state.exportLoading = true;
        state.exportError = null;
      })
      .addCase(exportRFI.fulfilled, (state) => {
        state.exportLoading = false;
      })
      .addCase(exportRFI.rejected, (state, action) => {
        state.exportLoading = false;
        state.exportError = action.payload;
      });
  },
});

export const { clearError, clearSuccess, clearSearchResults, clearExportState } = responseSlice.actions;
export default responseSlice.reducer;