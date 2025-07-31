import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { uploadFileApi } from "../../end-points/uploadFile";

// Async thunk for uploading file and getting markdown
export const uploadFileAndGetMarkdown = createAsyncThunk(
  'file/uploadFileAndGetMarkdown',
  async ({ file, user = 'RFP_Coordinator' }, { rejectWithValue }) => {
    try {
      const res = await uploadFileApi(file, user);
      return {
        mdFileExtract: res.mdFileExtract,
        success: res.success || true,
        mockResponse: res.mockResponse || false,
        timestamp: res.timestamp || new Date().toISOString()
      };
    } catch (err) {
      console.error('Upload failed', err);
      return rejectWithValue(err.message || 'Upload failed');
    }
  }
);

const initialState = {
  uploadedFile: null, 
  mdContent: '',
  loading: false,
  error: null,
  uploadInfo: null,
};

const fileSlice = createSlice({
  name: 'file',
  initialState,
  reducers: {
    setUploadedFile: (state, action) => {
      // action.payload is now serializable file info, not File object
      state.uploadedFile = action.payload;
    },
    setMdContent: (state, action) => {
      state.mdContent = action.payload;
    },
    clearUploadedFile: (state) => {
      state.uploadedFile = null;
      state.mdContent = '';
      state.error = null;
      state.uploadInfo = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(uploadFileAndGetMarkdown.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(uploadFileAndGetMarkdown.fulfilled, (state, action) => {
        state.loading = false;
        state.mdContent = action.payload.mdFileExtract;
        state.uploadInfo = {
          success: action.payload.success,
          timestamp: action.payload.timestamp
        };
      })
      .addCase(uploadFileAndGetMarkdown.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || action.error.message;
      });
  },
});

export const { setUploadedFile, setMdContent, clearUploadedFile } = fileSlice.actions;
export default fileSlice.reducer;