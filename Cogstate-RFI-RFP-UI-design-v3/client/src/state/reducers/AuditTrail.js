import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { getAuditTrailApi } from "../../end-points/AuditTrail";

const initialState = {
  loading: false,
  error: null,
  success: false,
  auditTrail: [], // Removed localStorage caching
};

export const getAuditTrail = createAsyncThunk(
  "auditTrail/getAuditTrail",
  async (payload, thunkAPI) => {
    try {
      const response = await getAuditTrailApi(payload);
      return response;
    } catch (error) {
      return thunkAPI.rejectWithValue(
        error.response?.data || "Failed to fetch query list"
      );
    }
  }
);

const getAuditTrailSlice = createSlice({
  name: "auditTrail",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(getAuditTrail.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getAuditTrail.fulfilled, (state, action) => {
        state.loading = false;
        state.success = true;
        state.error = null;
        state.auditTrail = action.payload; // Store data in auditTrail
        console.log("AuditTrail Reducer - Fulfilled:", action.payload);
      })
      .addCase(getAuditTrail.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "An error occurred";
        state.success = false;
        console.log("AuditTrail Reducer - Rejected:", action.payload);
      });
  },
});

export default getAuditTrailSlice.reducer;