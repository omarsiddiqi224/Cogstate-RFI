import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { activeRFIListApi, getRFIDetailsApi } from "../../end-points/rfi";

const initialState = {
  loading: false,
  error: null,
  activeProjects: [],
  responseDetails: null,
  responseDetailsLoading: false,
  responseDetailsError: null,
};

export const activeRFIList = createAsyncThunk(
  "rfi/activeRFIList",
  async (_, thunkAPI) => {
    try {
      const response = await activeRFIListApi();
      return response;
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error.response?.data || "Failed to fetch RFI list"
      );
    }
  }
);

export const getRFIDetails = createAsyncThunk(
  "rfi/getRFIDetails",
  async (responseId, thunkAPI) => {
    try {
      const response = await getRFIDetailsApi(responseId);
      return response;
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error.response?.data || "Failed to fetch RFI details"
      );
    }
  }
);

const rfiSlice = createSlice({
  name: "rfi",
  initialState,
  reducers: {
    clearResponseDetails: (state) => {
      state.responseDetails = null;
      state.responseDetailsError = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Active RFI List cases
      .addCase(activeRFIList.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(activeRFIList.fulfilled, (state, action) => {
        state.loading = false;
        state.activeProjects = action.payload;
      })
      .addCase(activeRFIList.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // RFI Details cases
      .addCase(getRFIDetails.pending, (state) => {
        state.responseDetailsLoading = true;
        state.responseDetailsError = null;
      })
      .addCase(getRFIDetails.fulfilled, (state, action) => {
        state.responseDetailsLoading = false;
        state.responseDetails = action.payload;
      })
      .addCase(getRFIDetails.rejected, (state, action) => {
        state.responseDetailsLoading = false;
        state.responseDetailsError = action.payload;
      });
  },
});

export const { clearResponseDetails } = rfiSlice.actions;
export default rfiSlice.reducer;