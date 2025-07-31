import axios from "../utils/axios-interceptor";

// Helper function to extract file extension from MIME type
const getFileExtension = (mimeType) => {
  const mimeToExtension = {
    'application/pdf': 'pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/msword': 'doc',
    'application/vnd.ms-excel': 'xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'text/markdown': 'md'
  };
  
  return mimeToExtension[mimeType] || 'unknown';
};

// File size limit in bytes (10MB)
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export const validateFileSize = (file) => {
  if (file.size > MAX_FILE_SIZE) {
    throw new Error(`File size exceeds the maximum limit of 10MB. Current file size: ${(file.size / (1024 * 1024)).toFixed(2)}MB`);
  }
  return true;
};

export const uploadFileApi = async (file, user = 'test') => {
  try {
    // Validate file size before upload
    validateFileSize(file);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('fileName', file.name);
    formData.append('fileType', getFileExtension(file.type)); // Changed to send extension only
    formData.append('size', file.size);
    formData.append('user', user); 

    const res = await axios.post('/draft-answers', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  } catch (error) {
    console.error('Upload API error, using mock data:', error);
    throw error; 
  }
};

export const getSerializableFileInfo = (file) => ({
  name: file.name,
  type: file.type,
  size: file.size,
  lastModified: file.lastModified,
  lastModifiedDate: file.lastModified ? new Date(file.lastModified).toISOString() : null
});