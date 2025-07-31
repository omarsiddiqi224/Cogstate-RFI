// Enhanced knowledgeBase.js API endpoint with debugging
import axios from "../utils/axios-interceptor";

export const submitKnowledgeBaseEntry = async (entryData) => {
  try {
    // Debug: Log the incoming data
    console.log('Submitting entry data:', entryData);

    const formData = new FormData();

    // Add form fields to FormData (matching server expectations)
    const entryTypeMapping = {
      'ORGANIZATIONAL_FACT': 'organizational_fact',
      'HR_DETAIL': 'hr_detail',
      'FINANCIAL': 'financial',
      'SERVICE': 'service',
      'SOP': 'sop',
      'POLICY': 'policy',
      'PAST_RESPONSE': 'past_response'
    };

    const mappedEntryType = entryTypeMapping[entryData.entryType.toUpperCase()] || entryData.entryType;
    formData.append('entryType', mappedEntryType);
    console.log('Entry type being sent:', entryData.entryType);

    if (entryData.serviceName) {
      formData.append('serviceName', entryData.serviceName);
      console.log('Service name:', entryData.serviceName);
    }
    if (entryData.serviceCategory) {
      formData.append('serviceCategory', entryData.serviceCategory);
      console.log('Service category:', entryData.serviceCategory);
    }

    if (!entryData.description || entryData.description.trim() === '') {
      throw new Error('Description is required and cannot be empty');
    }
    formData.append('description', entryData.description);
    console.log('Description length:', entryData.description.length);

    if (!entryData.tags || entryData.tags.trim() === '') {
      console.warn('Tags field is empty');
      formData.append('tags', '');
    } else {
      formData.append('tags', entryData.tags);
      console.log('Tags:', entryData.tags);
    }

    if (entryData.attachments && entryData.attachments.length > 0) {
      console.log('Number of attachments:', entryData.attachments.length);
      entryData.attachments.forEach((attachment, index) => {
        if (attachment.file) {
          formData.append('attachments', attachment.file);
          console.log(`Attachment ${index}:`, attachment.file.name, attachment.file.size, 'bytes');

          if (attachment.file.size > 10 * 1024 * 1024) {
            throw new Error(`File ${attachment.file.name} exceeds 10MB limit`);
          }
        }
      });
    } else {
      console.log('No attachments to upload');
    }

    console.log('FormData contents:');
    for (let pair of formData.entries()) {
      if (pair[1] instanceof File) {
        console.log(pair[0], ':', pair[1].name, '(File)');
      } else {
        console.log(pair[0], ':', pair[1]);
      }
    }

    console.log('Making API request to /addKnowledgeBase...');

    const res = await axios.post('/addKnowledgeBase', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      transformResponse: [(data) => {
        console.log('Raw response data:', data);
        if (!data || data.trim() === '') {
          return { success: true, message: 'Entry submitted successfully' };
        }
        try {
          return JSON.parse(data);
        } catch (error) {
          console.warn('Invalid JSON response, assuming success:', data);
          return { success: true, message: 'Entry submitted successfully' };
        }
      }]
    });

    console.log('API Response:', res.data);
    return res.data;

  } catch (error) {
    console.error('Submission API error:', error);

    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response headers:', error.response.headers);
      console.error('Response data:', error.response.data);

      let errorMessage = `Server error: ${error.response.status} ${error.response.statusText}`;
      if (error.response.data) {
        if (typeof error.response.data === 'string') {
          errorMessage += ` - ${error.response.data}`;
        } else if (error.response.data.message) {
          errorMessage += ` - ${error.response.data.message}`;
        } else if (error.response.data.error) {
          errorMessage += ` - ${error.response.data.error}`;
        }
      }

      throw new Error(errorMessage);
    } else if (error.request) {
      console.error('Request details:', error.request);
      throw new Error('Network error: No response from server');
    } else {
      console.error('Error details:', error.message);
      throw new Error(`Request error: ${error.message}`);
    }
  }
};

// Alternative version with validation
export const submitKnowledgeBaseEntryWithValidation = async (entryData) => {
  const errors = [];

  if (!entryData.entryType) {
    errors.push('Entry type is required');
  }

  if (!entryData.description || entryData.description.trim() === '') {
    errors.push('Description is required');
  }

  if (entryData.entryType === 'service') {
    if (!entryData.serviceName || entryData.serviceName.trim() === '') {
      errors.push('Service name is required for service entries');
    }
    if (!entryData.serviceCategory || entryData.serviceCategory.trim() === '') {
      errors.push('Service category is required for service entries');
    }
  }

  if (entryData.attachments && entryData.attachments.length > 0) {
    entryData.attachments.forEach((attachment) => {
      if (attachment.file && attachment.file.size > 10 * 1024 * 1024) {
        errors.push(`File "${attachment.file.name}" exceeds 10MB limit`);
      }
    });
  }

  if (errors.length > 0) {
    throw new Error(`Validation errors: ${errors.join(', ')}`);
  }

  return await submitKnowledgeBaseEntry(entryData);
};
