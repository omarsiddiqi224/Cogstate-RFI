// React and third-party imports
import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Search, Plus, FileUp, Paperclip, Trash2, Loader2 } from 'lucide-react';

// Local imports
import { submitKnowledgeBase, clearSubmissionState, resetForm } from '../state/reducers/knowledgeBase';
import 'react-draft-wysiwyg/dist/react-draft-wysiwyg.css';

/**
 * KnowledgeBase Component
 * 
 * Main page for managing knowledge base entries. Provides functionality to:
 * - View existing knowledge base entries (placeholder)
 * - Add new knowledge base entries with various types
 * - Upload attachments via drag-and-drop or file selection
 * - Submit entries for approval
 * - Handle form validation and submission states
 */
export default function KnowledgeBase() {
  // Redux hooks
  const dispatch = useDispatch();

  // Get Redux state for submission handling
  const { isSubmitting, submitSuccess, submitError, response } = useSelector((state) => state.kb);

  // UI state management
  const [searchQuery, setSearchQuery] = useState(''); // Search input for knowledge base entries
  const [viewMode, setViewMode] = useState('LIST'); // Toggle between LIST view and ADD_FORM view

  // Form state management
  const [entryType, setEntryType] = useState('service'); // Type of knowledge base entry
  const [serviceName, setServiceName] = useState(''); // Service name (for service entries)
  const [serviceCategory, setServiceCategory] = useState(''); // Service category selection
  const [detailedDescription, setDetailedDescription] = useState(''); // Main content description
  const [tags, setTags] = useState(''); // Comma-separated tags for categorization

  // Tag suggestion functionality (currently simulated)
  const [isSuggestingTags, setIsSuggestingTags] = useState(false); // Loading state for tag suggestions
  const [tagSuggestionError, setTagSuggestionError] = useState(''); // Error state for tag suggestions

  // File upload management
  const [attachments, setAttachments] = useState([]); // Array of uploaded files
  const [dragActive, setDragActive] = useState(false); // Drag-and-drop visual feedback

  // Modal state management
  const [showSuccessModal, setShowSuccessModal] = useState(false); // Success modal visibility
  const [successMessage, setSuccessMessage] = useState(''); // Success message from API


  /**
   * Handle successful form submission
   * Shows success modal and clears Redux submission state
   */
  useEffect(() => {
    if (submitSuccess) {
      // Use message from API response, fallback to default message
      const messageFromApi = response?.message || 'Knowledge base entry submitted successfully for approval!';
      setSuccessMessage(messageFromApi);
      setShowSuccessModal(true);

      // Clear submission state to prevent modal from showing again
      dispatch(clearSubmissionState());
    }
  }, [submitSuccess, dispatch, response]);

  /**
   * Switch to add new entry form view
   */
  const handleAddNewEntry = () => {
    setViewMode('ADD_FORM');
  };

  /**
   * Cancel form submission and reset all form fields
   * Returns to list view and clears all input data
   */
  const handleCancel = () => {
    setEntryType('service');
    setServiceName('');
    setServiceCategory('');
    setDetailedDescription('');
    setTags('');
    setAttachments([]);
    setViewMode('LIST');
  };

  /**
   * Handle file upload from input element
   * Creates file objects with unique IDs and stores actual file for submission
   */
  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files).map((file, index) => ({
      id: `${file.name}-${Date.now()}-${index}`, // Unique ID for React keys
      name: file.name,
      file: file // Store the actual file object for submission
    }));
    setAttachments((prev) => [...prev, ...files]);
  };

  /**
   * Remove attachment from the list by ID
   */
  const removeAttachment = (id) => {
    setAttachments((prev) => prev.filter((file) => file.id !== id));
  };

  /**
   * Generate tag suggestions based on entry content
   * Currently simulated - would call AI service in production
   */
  const handleSuggestTags = () => {
    setIsSuggestingTags(true);
    setTagSuggestionError('');

    // Simulate API call for tag suggestions
    setTimeout(() => {
      const suggestedTags = 'sample, suggested, tags';
      setTags(suggestedTags);
      setIsSuggestingTags(false);
    }, 1000);
  };

  /**
   * Submit knowledge base entry for approval
   * Prepares form data and dispatches Redux action
   */
  const handleSubmitForApproval = async (e) => {
    e.preventDefault();

    try {
      // Prepare entry data for API submission
      const entryData = {
        entryType: entryType.toLowerCase(),
        serviceName,
        serviceCategory,
        description: detailedDescription,
        tags,
        attachments
      };

      // Use Redux thunk for submission
      dispatch(submitKnowledgeBase(entryData));

    } catch (error) {
      console.error('Submission error:', error);
    }
  };

  /**
   * Close success modal and refresh page
   * Refreshes to clear all form state and return to clean list view
   */
  const handleModalClose = () => {
    setShowSuccessModal(false);
    // Refresh the page to clear all state
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-light-gray">
      {/* Page header with title and search */}
      <div className="bg-white px-6 py-4 flex flex-row justify-between border-b">
        <h1 className="text-xl font-bold text-primary flex-1">KnowledgeBase</h1>
        <div className="flex-1">
          {/* Search input for knowledge base entries */}
          <div className="relative w-full">
            <Search size={24} strokeWidth={1.5} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-secondary" />
            <input
              type="text"
              placeholder="Search Knowledge Base ..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-secondary"
            />
          </div>
        </div>
      </div>

      {/* Main content area - switches between list and form views */}
      {/* List view - placeholder for future knowledge base entries display */}
      {viewMode === 'LIST' && (
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-800">Knowledge Base Suggestions</h2>

              {/* Button to switch to add form view */}
              <button
                className="bg-secondary hover:bg-blue-700 text-white px-4 py-2 rounded-full flex items-center gap-2"
                onClick={handleAddNewEntry}
              >
                <Plus size={20} strokeWidth={1.5} className="text-white" />
                Add New Entry
              </button>
            </div>
            {/* Placeholder content - would show actual entries in production */}
            <div className="text-gray-600 mb-4">
              Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium...
            </div>
            <ul className="text-gray-600 space-y-1">
              <li>• View existing knowledge articles</li>
              <li>• Filter by category, tags</li>
              <li>• Search articles</li>
            </ul>
          </div>
        </div>
      )}

      {/* Add new entry form view */}
      {viewMode === 'ADD_FORM' && (
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h1 className="text-2xl font-semibold text-gray-800 mb-2">Knowledge Base</h1>
            <p className="text-sm text-secondary mb-6 font-medium"><span className='uppercase'>Knowledge Base</span> &gt; Add New Entry</p>

            {/* Main form for knowledge base entry creation */}
            <form onSubmit={handleSubmitForApproval}>
              {/* Entry type selection */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <label htmlFor="entryType" className="block text-sm font-medium mb-1">Entry Type</label>
                  <select
                    id="entryType"
                    value={entryType}
                    onChange={(e) => setEntryType(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-secondary"
                    required
                  >
                    <option value="organizational_fact">Organizational Fact</option>
                    <option value="hr_detail">HR Detail</option>
                    <option value="financial">Financial Detail</option>
                    <option value="service">Service</option>
                    <option value="sop">SOP</option>
                    <option value="policy">Policy</option>
                    <option value="past_response">Past Response</option>
                  </select>
                </div>
              </div>

              {/* Service-specific fields - only shown when service type is selected */}
              {(entryType === 'service' || entryType === 'service') && (
                <>
                  <div className="mb-6">
                    <label className="block text-sm font-medium mb-1">Service Name</label>
                    <input
                      type="text"
                      value={serviceName}
                      onChange={(e) => setServiceName(e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-secondary"
                      required
                    />
                  </div>
                  <div className="mb-6">
                    <label className="block text-sm font-medium mb-1">Service Category</label>
                    <select
                      value={serviceCategory}
                      onChange={(e) => setServiceCategory(e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-secondary"
                      required
                    >
                      <option value="">Select Category...</option>
                      <option value="clinical_Operations">Clinical Operations</option>
                      <option value="data_Management">Data Management</option>
                      <option value="regulatory_Affairs">Regulatory Affairs</option>
                    </select>
                  </div>
                </>
              )}

              {/* Main content description field */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-1">Detailed Description</label>
                <textarea
                  className="w-full h-32 p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-secondary"
                  value={detailedDescription}
                  onChange={(e) => setDetailedDescription(e.target.value)}
                  placeholder="Enter details here..."
                  disabled={isSubmitting}
                  required
                />
              </div>

              {/* Tags input with optional AI suggestion feature */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-1">Tags</label>
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={tags}
                    onChange={(e) => setTags(e.target.value)}
                    className="flex-1 p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-secondary"
                    disabled={isSuggestingTags || isSubmitting}
                    placeholder="Enter tags separated by commas..."
                  />
                  {/* Tag suggestion button - currently commented out */}
                  {/* {entryType === 'service' && (
                    <button
                      type="button"
                      onClick={handleSuggestTags}
                      disabled={isSuggestingTags || isSubmitting}
                      className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 flex items-center gap-2"
                    >
                      {isSuggestingTags ? (
                        <>
                          <Loader2 size={16} strokeWidth={1} className="animate-spin" />
                          Suggesting...
                        </>
                      ) : (
                        'Suggest Tags'
                      )}
                    </button>
                  )} */}
                </div>
                {tagSuggestionError && <p className="text-red-500 text-sm mt-1">{tagSuggestionError}</p>}
              </div>

              {/* File upload section with drag-and-drop functionality */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-1">Attachments</label>
                <div
                  className={`flex-1 cursor-pointer flex flex-col items-center justify-center border-2 border-dashed border-secondary rounded-xl p-6 hover:bg-secondary/5 transition ${dragActive
                    ? 'border-secondary bg-blue-50'
                    : 'border-gray-300 hover:border-secondary/75'
                    }`}
                  onClick={() => document.getElementById('file-upload').click()}
                  // Drag and drop event handlers
                  onDragEnter={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setDragActive(true);
                  }}
                  onDragLeave={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setDragActive(false);
                  }}
                  onDragOver={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setDragActive(true);
                  }}
                  onDrop={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setDragActive(false);
                    // Process dropped files
                    const droppedFiles = Array.from(e.dataTransfer.files).map((file, index) => ({
                      id: `${file.name}-${Date.now()}-${index}`,
                      name: file.name,
                      file: file
                    }));
                    setAttachments((prev) => [...prev, ...droppedFiles]);
                  }}
                >
                  {/* Upload area visual elements */}
                  <FileUp size={32} strokeWidth={1} className="mx-auto text-secondary" />
                  <p className="text-sm font-medium text-secondary">Click to select a file</p>
                  <p className="text-sm text-secondary mb-4">or drag and drop</p>
                  <p className="text-xs text-gray-500 italic">Maximum file size is 10 MB</p>
                  {/* Hidden file input */}
                  <input
                    id="file-upload"
                    type="file"
                    multiple
                    className="inset-0 opacity-0 cursor-pointer"
                    onChange={handleFileUpload}
                    disabled={isSubmitting}
                  />
                </div>

                {/* List of uploaded attachments */}
                {attachments.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {attachments.map(file => (
                      <li
                        key={file.id}
                        className="flex justify-between items-center text-sm bg-gray-100 p-2 rounded"
                      >
                        <span className="flex items-center gap-2">
                          <Paperclip size={14} strokeWidth={1} /> {file.name}
                        </span>
                        {/* Remove attachment button */}
                        <button
                          type="button"
                          onClick={() => removeAttachment(file.id)}
                          className="text-red-500 hover:text-red-700 disabled:opacity-50"
                          disabled={isSubmitting}
                        >
                          <Trash2 size={14} strokeWidth={1} />
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Error message display */}
              {submitError && (
                <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                  {submitError}
                </div>
              )}

              {/* Form action buttons */}
              <div className="flex justify-end gap-3 mt-4 pt-4 border-t">
                {/* Cancel button - resets form and returns to list */}
                <button
                  type="button"
                  onClick={handleCancel}
                  className="py-2 px-10 rounded-full font-medium text-xs uppercase transition-colors border border-secondary bg-white text-secondary hover:bg-secondary/25"
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                {/* Save Draft button - currently commented out */}
                {/* <button
                  type="button"
                  className="py-2 px-10 rounded-full font-medium text-xs uppercase transition-colors border border-secondary bg-white text-secondary hover:bg-secondary/25"
                  disabled={isSubmitting}
                >
                  Save Draft
                </button> */}
                {/* Submit button with loading state */}
                <button
                  type="submit"
                  className="py-2 px-10 rounded-full font-medium text-xs uppercase transition-colors bg-secondary text-white hover:bg-blue-700 disabled:bg-gray-400"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 size={16} strokeWidth={1} className="animate-spin inline mr-2" />
                      Submitting...
                    </>
                  ) : (
                    'Submit for Approval'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* Success modal - shown after successful submission */}
      {showSuccessModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
            <div className="text-center">
              {/* Success icon */}
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Success!</h3>
              <p className="text-gray-600 mb-6">{successMessage}</p>
              {/* Close modal button - refreshes page */}
              <button
                onClick={handleModalClose}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </div>

  );
}