import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { useParams, useNavigate } from 'react-router-dom';
import MDEditor from '@uiw/react-md-editor';
import SimpleBar from 'simplebar-react';
import 'simplebar-react/dist/simplebar.min.css';
import '@uiw/react-md-editor/markdown-editor.css';
import { FileText, Save, CheckCircle, Search, Plus, Eye, ChevronLeft, ChevronRight, Check, Pencil, UserPlus, X } from 'lucide-react';

import AuditTrail from '../components/AuditTrail';
import { generateDraft, saveSection, markComplete, submitReview, searchKnoweledgeBase } from '../state/reducers/ResponsePage';


export default function ResponsePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [response, setResponse] = useState(null);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [selectedQuestionIndex, setSelectedQuestionIndex] = useState(0);
  const [editedMarkdown, setEditedMarkdown] = useState('');
  const [originalMarkdown, setOriginalMarkdown] = useState('');

  const [activeTab, setActiveTab] = useState('document-sections');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAllSuggestions, setShowAllSuggestions] = useState(false);
  const [visibleFullText, setVisibleFullText] = useState(null);

  const [searchResults, setSearchResults] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);

  const [reviewMessage, setReviewMessage] = useState('');
  const [showReviewModal, setShowReviewModal] = useState(false);

  const tabs = [
    { id: 'document-sections', label: 'Document Sections' },
    { id: 'team-chat', label: 'Team Chat' },
    { id: 'knowledge-search', label: 'Knowledge Search' },
    { id: 'audit-trail', label: 'Audit Trail' }
  ];

  const knowledgeBaseSuggestions = selectedQuestion?.knowledgeBase || [];

  useEffect(() => {
    const data = localStorage.getItem(`response_${id}`);
    if (data) {
      const parsed = JSON.parse(data);
      setResponse(parsed);
      setSelectedQuestion(parsed.questions[0]);
      setSelectedQuestionIndex(0);
      setEditedMarkdown(parsed.questions[0].response);
    }
  }, [id]);

  useEffect(() => {
    if (selectedQuestion) {
      setEditedMarkdown(selectedQuestion.response);
      setOriginalMarkdown(selectedQuestion.response);

      if (selectedQuestion.searchResults) {
        setSearchResults(selectedQuestion.searchResults);
        setShowSearchResults(true);
      } else {
        setSearchResults([]);
        setShowSearchResults(false);
      }
    }
  }, [selectedQuestion]);

  const handleSearch = async (searchText) => {
    if (!searchText.trim()) return;

    try {
      const payload = { searchText: searchText.trim() };
      const result = await dispatch(searchKnoweledgeBase(payload));

      if (searchKnoweledgeBase.fulfilled.match(result)) {
        const searchData = result.payload;

        const updatedQuestions = [...response.questions];
        updatedQuestions[selectedQuestionIndex] = {
          ...updatedQuestions[selectedQuestionIndex],
          searchResults: searchData
        };

        const updatedResponse = {
          ...response,
          questions: updatedQuestions
        };

        setResponse(updatedResponse);
        setSelectedQuestion(updatedQuestions[selectedQuestionIndex]);
        setSearchResults(searchData);
        setShowSearchResults(true);
      } else {
        console.error('Failed to search:', result.payload);
      }
    } catch (error) {
      console.error('Search error:', error);
    }
  };

  const handleClearSearch = () => {
    const updatedQuestions = [...response.questions];
    const { searchResults, ...questionWithoutSearch } = updatedQuestions[selectedQuestionIndex];
    updatedQuestions[selectedQuestionIndex] = questionWithoutSearch;

    const updatedResponse = {
      ...response,
      questions: updatedQuestions
    };

    setResponse(updatedResponse);
    setSelectedQuestion(updatedQuestions[selectedQuestionIndex]);
    setSearchResults([]);
    setShowSearchResults(false);
    setSearchQuery('');
  };

  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch(searchQuery);
    }
  };

  const handleGenerateDraft = async () => {
    if (!selectedQuestion || !response?.id) return;

    const payload = {
      responseId: response.metaData?.source_document_id || response.id,
      questionId: String(selectedQuestion.id),
      question: selectedQuestion.question,
      response: editedMarkdown,
      status: "Draft",
      user: "Alice"
    };

    const result = await dispatch(generateDraft(payload));

    if (generateDraft.fulfilled.match(result)) {
      const updatedData = result.payload.data;

      const updatedQuestions = [...response.questions];
      updatedQuestions[selectedQuestionIndex] = {
        ...updatedQuestions[selectedQuestionIndex],
        ...updatedData
      };

      const updatedResponse = {
        ...response,
        questions: updatedQuestions
      };

      setResponse(updatedResponse);
      setSelectedQuestion(updatedQuestions[selectedQuestionIndex]);
      setEditedMarkdown(updatedData.response);
    } else {
      console.error('Failed to generate draft:', result.payload);
    }
  };

  const handleSaveSection = async () => {
    if (!selectedQuestion || !response?.id) return;

    const payload = {
      responseId: response.metaData?.source_document_id || response.id,
      questionId: String(selectedQuestion.id),
      question: selectedQuestion.question,
      response: editedMarkdown,
      status: "Save",
      user: "Alice"
    };

    const result = await dispatch(saveSection(payload));

    if (saveSection.fulfilled.match(result)) {
      const updatedData = result.payload.data;

      const updatedQuestions = [...response.questions];
      updatedQuestions[selectedQuestionIndex] = {
        ...updatedQuestions[selectedQuestionIndex],
        ...updatedData
      };

      const updatedResponse = {
        ...response,
        questions: updatedQuestions
      };

      setResponse(updatedResponse);
      setSelectedQuestion(updatedQuestions[selectedQuestionIndex]);
      setEditedMarkdown(updatedData.response);
      setOriginalMarkdown(updatedData.response);
    } else {
      console.error('Failed to save section:', result.payload);
    }
  };

  const handleMarkComplete = async () => {
    if (!selectedQuestion || !response?.id) return;

    const payload = {
      responseId: response.metaData?.source_document_id || response.id,
      questionId: String(selectedQuestion.id),
      question: selectedQuestion.question,
      response: editedMarkdown,
      status: "Completed",
      user: "Alice"
    };

    const result = await dispatch(markComplete(payload));

    if (markComplete.fulfilled.match(result)) {
      const updatedData = result.payload.data;

      const updatedQuestions = [...response.questions];
      updatedQuestions[selectedQuestionIndex] = {
        ...updatedQuestions[selectedQuestionIndex],
        ...updatedData
      };

      const updatedResponse = {
        ...response,
        questions: updatedQuestions
      };

      setResponse(updatedResponse);
      setSelectedQuestion(updatedQuestions[selectedQuestionIndex]);
      setEditedMarkdown(updatedData.response);
    } else {
      console.error('Failed to mark complete:', result.payload);
    }
  };

  /**
   * Submit the entire response for review
   * Shows a modal with success/failure message
   */
  const handleSubmitReview = async () => {
    if (!response?.id) return;

    const payload = {
      responseId: response.metaData?.source_document_id || response.id,
      status: 'submitReview',
      user: 'Bob'
    };

    const result = await dispatch(submitReview(payload));

    if (submitReview.fulfilled.match(result)) {
      const { message } = result.payload;
      setReviewMessage(message || 'Submitted successfully!');
      setShowReviewModal(true);

      // Auto-hide modal after 5 seconds
      setTimeout(() => {
        setShowReviewModal(false);
      }, 5000);
    } else {
      setReviewMessage('Failed to submit review.');
      setShowReviewModal(true);
      setTimeout(() => {
        setShowReviewModal(false);
      }, 5000);
    }
  };

  /**
   * Insert knowledge base suggestion into the editor
   */
  const handleInsertSuggestion = (suggestion) => {
    const answerOnly = suggestion.fullText?.split('\n\nAnswer:')[1]?.trim() || '';
    setEditedMarkdown(prev => prev + '\n\n' + answerOnly);
  };

  /**
   * Toggle visibility of full suggestion text for comparison
   */
  const handleViewFullSuggestion = (suggestion) => {
    setVisibleFullText(visibleFullText === suggestion.id ? null : suggestion.id);
  };

  /**
   * Navigate back to previous page
   */
  const handleBack = () => {
    navigate(-1);
  };

  /**
   * Navigate to RFI/RFP list page
   */
  const handleNavigateToRfiRfp = () => {
    navigate('/rfi-rfp');
  };

  /**
   * Navigate to previous question
   * Reverts unsaved changes before switching
   */
  const handlePreviousQuestion = () => {
    if (response && selectedQuestionIndex > 0) {
      // Revert to original if not saved
      if (editedMarkdown !== originalMarkdown) {
        const updatedQuestions = [...response.questions];
        updatedQuestions[selectedQuestionIndex] = {
          ...updatedQuestions[selectedQuestionIndex],
          response: originalMarkdown
        };
        setResponse({ ...response, questions: updatedQuestions });
      }

      // Clear search results when switching questions
      setSearchResults([]);
      setShowSearchResults(false);
      setSearchQuery('');
      setVisibleFullText(null);

      const newIndex = selectedQuestionIndex - 1;
      setSelectedQuestionIndex(newIndex);
      setSelectedQuestion(response.questions[newIndex]);
    }
  };

  /**
   * Navigate to next question
   * Reverts unsaved changes before switching
   */
  const handleNextQuestion = () => {
    if (response && selectedQuestionIndex < response.questions.length - 1) {
      // Revert to original if not saved
      if (editedMarkdown !== originalMarkdown) {
        const updatedQuestions = [...response.questions];
        updatedQuestions[selectedQuestionIndex] = {
          ...updatedQuestions[selectedQuestionIndex],
          response: originalMarkdown
        };
        setResponse({ ...response, questions: updatedQuestions });
      }

      // Clear search results when switching questions
      setSearchResults([]);
      setShowSearchResults(false);
      setSearchQuery('');
      setVisibleFullText(null);

      const newIndex = selectedQuestionIndex + 1;
      setSelectedQuestionIndex(newIndex);
      setSelectedQuestion(response.questions[newIndex]);
    }
  };

  /**
   * Select a specific question from the list
   * Reverts unsaved changes before switching
   */
  const handleQuestionSelect = (question, index) => {
    // Revert to original if not saved
    if (editedMarkdown !== originalMarkdown) {
      const updatedQuestions = [...response.questions];
      updatedQuestions[selectedQuestionIndex] = {
        ...updatedQuestions[selectedQuestionIndex],
        response: originalMarkdown
      };
      setResponse({ ...response, questions: updatedQuestions });
    }

    // Clear search results when switching questions
    setSearchResults([]);
    setShowSearchResults(false);
    setSearchQuery('');
    setVisibleFullText(null);

    setSelectedQuestion(question);
    setSelectedQuestionIndex(index);
  };

  // Show loading state while response data is being fetched
  if (!response) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  /**
   * Render content based on active tab
   * Main content switching logic for different views
   */
  const renderTabContent = () => {
    switch (activeTab) {
      case 'document-sections':
        return (
          <div className="flex flex-col bg-light-gray" style={{ height: 'calc(100vh - 200px)' }}>
            {/* Progress indicator section */}
            <div className="flex justify-end px-4 py-2">
              <div className="hidden">Autosave</div>
              <div className="flex items-center gap-4">
                <span className="text-[10px] text-gray-600">Progress: {response.progress}%</span>
                <div className="w-36 h-2 bg-gray-200 rounded-full">
                  <div
                    className="h-2 bg-secondary rounded-full transition-all duration-300"
                    style={{ width: `${response.progress}%` }}
                  ></div>
                </div>
              </div>
            </div>

            {/* Main content area with left and right panels */}
            <div className="flex gap-6 px-4 pb-4" style={{ height: 'calc(100vh - 200px)' }} >
              {/* Left Panel - Questions List */}
              <div className="w-1/3 flex flex-col bg-white border border-gray-200 rounded-lg overflow-hidden mb-4 shadow-md">
                <div className="p-4 border-b border-gray-200 flex-shrink-0">
                  <h3 className="text-sm font-semibold text-primary">Client Questions</h3>
                </div>
                <SimpleBar style={{ maxHeight: '100%' }} className="flex-1 pb-14">
                  {response.questions.map((q, index) => (
                    <div key={q.id} className='m-2 pb-2 border-b border-gray-100'>
                      <div
                        className={`px-4 py-2 cursor-pointer rounded-lg border hover:bg-gray-50 ${selectedQuestion?.id === q.id ? 'border-secondary shadow-md' : ' border-transparent'
                          }`}
                        onClick={() => handleQuestionSelect(q, index)}
                      >
                        <div className="flex items-center justify-between text-xs text-gray-500 mb-2 ">
                          <span
                            className={`p-1 text-[10px] font-medium ${q.status === 'completed'
                              ? 'bg-green-100 text-green-800 rounded-full'
                              : q.status === 'in-progress'
                                ? 'bg-yellow-100 text-yellow-800 rounded-lg '
                                : 'bg-gray-100 text-gray-800 rounded-lg '
                              }`}
                          >
                            {q.status === 'completed' ? <Check size={12} /> : q.status}
                          </span>
                          <span className="text-[10px] flex items-center gap-2">
                            {q.assignedTo ? q.assignedTo : (
                              <>
                                <UserPlus size={12} strokeWidth={1.5} />
                                Assign
                              </>
                            )}
                            <Pencil size={12} strokeWidth={1.5} className="text-secondary" />
                          </span>
                        </div>
                        <div className="text-xs font-medium line-clamp-2 flex justify-between gap-3">
                          <span className="font-bold text-primary whitespace-nowrap">{index + 1}</span>
                          <span className="text-xs flex-1">{q.question}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </SimpleBar>
              </div>

              {/* Right Panel - Question Editor and Knowledge Base */}
              <div className="w-2/3 overflow-y-auto mb-4 pr-2 flex flex-col">
                {selectedQuestion ? (
                  <div className="flex flex-col h-full">
                    {/* Question response editor section */}
                    <div className="border rounded-lg bg-white p-4 mb-4 shadow-md">
                      {/* Question header with navigation */}
                      <div className="mb-4 pb-2 border-b flex items-center justify-between">
                        <div className="flex-1">
                          <h4 className="text-sm font-semibold text-primary mb-1">
                            Response for: {selectedQuestionIndex + 1}.{' '}
                            {selectedQuestion?.question?.substring(0, 50)}...
                          </h4>
                        </div>
                        <div className="flex items-center gap-2 ml-4">
                          <button
                            onClick={handlePreviousQuestion}
                            disabled={selectedQuestionIndex === 0}
                            className="p-1 rounded-full text-secondary border border-gray-300 hover:bg-secondary/25 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <ChevronLeft size={14} strokeWidth={3} />
                          </button>
                          <button
                            onClick={handleNextQuestion}
                            disabled={selectedQuestionIndex === response.questions.length - 1}
                            className="p-1 rounded-full text-secondary border border-gray-300 hover:bg-secondary/25 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <ChevronRight size={14} strokeWidth={3} />
                          </button>
                        </div>
                      </div>

                      {/* Markdown editor for response content */}
                      <div className="flex-1 mb-4 bg-gray-200">
                        <MDEditor
                          value={editedMarkdown}
                          onChange={setEditedMarkdown}
                          preview="edit"
                          height={200}
                          className="!border-0 !shadow-none !rounded-lg"
                        />
                      </div>

                      {/* Action buttons for response management */}
                      <div className="flex justify-between flex-wrap items-center gap-3 mt-4">
                        {/* AI draft generation button */}
                        <button
                          onClick={handleGenerateDraft}
                          className="flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold text-white bg-gradient-to-r from-[#673aa1] to-secondary hover:from-secondary hover:to-[#673aa1]"
                        >
                          <FileText size={14} />
                          Generate Draft
                        </button>

                        {/* Save and complete buttons */}
                        <div className="flex gap-3">
                          <button
                            onClick={handleSaveSection}
                            className="flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold bg-white border border-gray-200 text-secondary hover:bg-secondary/15 hover:border-secondary"
                          >
                            <Save size={14} strokeWidth={1.5} className="text-secondary" />
                            Save Section
                          </button>

                          <button
                            onClick={handleMarkComplete}
                            className="flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold bg-white border border-gray-200 text-secondary hover:bg-secondary/15 hover:border-secondary"
                          >
                            <CheckCircle size={14} strokeWidth={1.5} className="text-secondary" />
                            Mark as Complete
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Knowledge Base Suggestions section */}
                    <div className="border rounded-lg bg-white p-4 mb-4 shadow-md">
                      <h4 className="mb-3">
                        <span className="font-semibold">
                          {showSearchResults ? 'Search Results' : 'Knowledge Base Suggestions'}
                        </span> ({showSearchResults ? searchResults.length : knowledgeBaseSuggestions.length} Results)
                      </h4>

                      {/* Search functionality for knowledge base */}
                      <div className="relative mb-4">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-secondary" size={16} />
                        <input
                          type="text"
                          placeholder="Search Knowledge Base..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          onKeyPress={handleSearchKeyPress}
                          className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary"
                        />
                      </div>

                      {/* List of knowledge base suggestions or search results */}
                      <div className="">
                        {showSearchResults ? (
                          // Search Results Section
                          <>
                            <div className="flex justify-between items-center mb-4">
                              <h5 className="text-sm font-semibold">Search Results ({searchResults.length} found)</h5>
                              <button
                                onClick={handleClearSearch}
                                className="flex items-center gap-1 px-3 py-1 text-xs rounded-full border border-gray-400 text-gray-700 hover:border-secondary hover:text-secondary transition"
                              >
                                <X size={12} className="text-secondary" /> Clear
                              </button>
                            </div>
                            {searchResults.length === 0 ? (
                              <div className="text-center py-8 text-gray-500">
                                <p className="text-sm">No search results found</p>
                              </div>
                            ) : (
                              searchResults.map((result) => (
                                <div
                                  key={result.id}
                                  className={`border-b border-gray-200 p-4 hover:bg-gray-100 ${visibleFullText === result.id ? 'bg-gray-100' : 'bg-white'}`}
                                >
                                  <div className="mb-1 text-sm">
                                    <span className="font-bold text-primary">{result.category}</span>{' '}
                                    <span className="text-gray-600 font-medium">: {result.title}</span>
                                  </div>
                                  <p className="text-sm text-gray-700 mb-3 line-clamp-3">{result.snippet}</p>
                                  {visibleFullText === result.id && (
                                    <div className="bg-white rounded-md p-3 mb-3 relative">
                                      <button
                                        onClick={() => setVisibleFullText(null)}
                                        className="absolute top-2 right-2 text-gray-500 hover:text-gray-700"
                                      >
                                        <X size={16} />
                                      </button>
                                      <h3 className="font-semibold text-xs">Comparison Analysis</h3>
                                      <div className="text-xs mb-2">Comparing with: {result.category} {result.title}</div>
                                      <div className="pr-6 border-[#f00] border p-2 rounded-md">
                                        <p className="uppercase text-xs mb-2 text-[#f00]">Different</p>
                                        {(() => {
            const parts = result.fullText.split('\n\nAnswer:');
            const questionText = parts[0]?.replace('Question:', '').trim();
            const answerText = parts[1]?.trim() || '';
            return (
              <div className="text-xs">
                <div className="mb-2">
                  <span className="font-semibold text-gray-800 mr-2">Question:</span>
                  <span>{questionText}</span>
                </div>
                <div>
                  <span className="font-semibold text-gray-800 mr-2">Answer:</span>
                  <span>{answerText}</span>
                </div>
              </div>
            );
          })()}
                                      </div>
                                    </div>
                                  )}
                                  <div className="flex justify-start items-center gap-3">
                                    <button
                                      onClick={() => handleInsertSuggestion(result)}
                                      className="flex items-center gap-1 px-3 py-1 text-xs rounded-full border border-gray-400 text-gray-700 hover:border-secondary hover:text-secondary transition"
                                    >
                                      <Plus size={12} className="text-secondary" /> Insert
                                    </button>
                                    <button
                                      onClick={() => handleViewFullSuggestion(result)}
                                      className="flex items-center gap-1 px-3 py-1 text-xs rounded-full border border-gray-400 text-gray-700 hover:border-secondary hover:text-secondary transition"
                                    >
                                      <Eye size={12} className="text-secondary" /> Compare
                                    </button>
                                  </div>
                                </div>
                              ))
                            )}
                          </>
                        ) : (
                          // Original Knowledge Base Suggestions Section
                          <>
                            {knowledgeBaseSuggestions.length === 0 ? (
                              <div className="text-center py-8 text-gray-500">
                                <p className="text-sm">No knowledge base suggestions available</p>
                              </div>
                            ) : (
                              (showAllSuggestions ? knowledgeBaseSuggestions : knowledgeBaseSuggestions.slice(0, 3)).map((suggestion) => (
                                <div
                                  key={suggestion.id}
                                  className={`border-b border-gray-200 p-4 hover:bg-gray-100 ${visibleFullText === suggestion.id ? 'bg-gray-100' : 'bg-white'}`}
                                >
                                  <div className="mb-1 text-sm">
                                    <span className="font-bold text-primary">{suggestion.category}</span>{' '}
                                    <span className="text-gray-600 font-medium">: {suggestion.title}</span>
                                  </div>
                                  <p className="text-sm text-gray-700 mb-3 line-clamp-3">{suggestion.snippet}</p>
                                  {visibleFullText === suggestion.id && (
                                    <div className="bg-white rounded-md p-3 mb-3 relative">
                                      <button
                                        onClick={() => setVisibleFullText(null)}
                                        className="absolute top-2 right-2 text-gray-500 hover:text-gray-700"
                                      >
                                        <X size={16} />
                                      </button>
                                      <h3 className="font-semibold text-xs">Comparison Analysis</h3>
                                      <div className="text-xs mb-2">Comparing with: {suggestion.category} {suggestion.title}</div>
                                      <div className="pr-6 border-[#f00] border p-2 rounded-md">
                                        <p className="uppercase text-xs mb-2 text-[#f00]">Different</p>
                                        {(() => {
            const parts = suggestion.fullText.split('\n\nAnswer:');
            const questionText = parts[0]?.replace('Question:', '').trim();
            const answerText = parts[1]?.trim() || '';
            return (
              <div className="text-xs">
                <div className="mb-2">
                  <span className="font-semibold text-gray-800 mr-2">Question:</span>
                  <span>{questionText}</span>
                </div>
                <div>
                  <span className="font-semibold text-gray-800 mr-2">Answer:</span>
                  <span>{answerText}</span>
                </div>
              </div>
            );
          })()}
                                      </div>
                                    </div>
                                  )}
                                  <div className="flex justify-start items-center gap-3">
                                    <button
                                      onClick={() => handleInsertSuggestion(suggestion)}
                                      className="flex items-center gap-1 px-3 py-1 text-xs rounded-full border border-gray-400 text-gray-700 hover:border-secondary hover:text-secondary transition"
                                    >
                                      <Plus size={12} className="text-secondary" /> Insert
                                    </button>
                                    <button
                                      onClick={() => handleViewFullSuggestion(suggestion)}
                                      className="flex items-center gap-1 px-3 py-1 text-xs rounded-full border border-gray-400 text-gray-700 hover:border-secondary hover:text-secondary transition"
                                    >
                                      <Eye size={12} className="text-secondary" /> Compare
                                    </button>
                                  </div>
                                </div>
                              ))
                            )}

                            {/* Toggle to show all suggestions */}
                            {knowledgeBaseSuggestions.length > 3 && !showAllSuggestions && (
                              <div className="text-center pt-4">
                                <button
                                  onClick={() => setShowAllSuggestions(true)}
                                  className="text-[10px] text-gray-950 font-semibold uppercase hover:underline"
                                >
                                  Show All
                                </button>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-gray-500">Select a question to see answer</div>
                )}
              </div>
            </div>
          </div>
        );

      // Team chat tab - placeholder for future implementation
      case 'team-chat':
        return (
          <div className="min-h-screen bg-light-gray">
            <div className="max-w-7xl mx-auto px-6 py-8">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Team Chat</h3>
                <p className='text-sm'>Team chat feature coming soon.</p>
              </div>
            </div>
          </div>
        );

      // Knowledge search tab - placeholder for future implementation
      case 'knowledge-search':
        return (
          <div className="min-h-screen bg-light-gray">
            <div className="max-w-7xl mx-auto px-6 py-8">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Knowledge Search</h3>
                <p className='text-sm'>Knowledge Search feature coming soon.</p>
              </div>
            </div>
          </div>
        );

      // Audit trail tab - shows response history and changes
      case 'audit-trail':
        return <AuditTrail responseId={id} />;

      default:
        return null;
    }
  };

  return (
    <section className="h-screen flex flex-col w-full">
      {/* Main header section */}
      <div>
        {/* Top header with breadcrumb navigation and action buttons */}
        <div className="bg-white px-4 py-3 border-b flex justify-between">
          <div className="flex flex-col gap-3">
            {/* Breadcrumb navigation */}
            <div className="flex items-center gap-2">
              <span
                onClick={handleNavigateToRfiRfp}
                className="text-xs text-secondary hover:underline cursor-pointer"
              >
                RFI/RFP Responses
              </span>
              <span className="text-gray-400"><ChevronRight size={14} strokeWidth={1.5} /></span>
              <span className="text-xs">Project: {response.title}</span>
            </div>
            {/* Page title */}
            <h1 className="text-xl font-bold text-primary">
              {response.section}
            </h1>
          </div>
          <div className="flex flex-col gap-1">
            {/* Due date display */}
            <div className="text-right">
              <span className="text-[10px]">Due Date: 05/26/2025</span>
            </div>
            {/* Action buttons */}
            <div className="flex items-center gap-4">
              <button className="px-4 py-2 rounded-full font-bold text-[10px] uppercase transition-colors border border-secondary bg-white text-secondary hover:bg-secondary/25 hover:border-secondary/25">
                Export Draft
              </button>
              <button
                onClick={handleSubmitReview}
                className="px-4 py-2 rounded-full font-bold text-[10px] uppercase transition-colors bg-secondary text-white hover:bg-blue-700 disabled:bg-secondary/25" disabled={response.progress !== 100}>
                Submit for Review
              </button>
            </div>
          </div>
        </div>

        {/* Tab navigation bar */}
        <div className="bg-primary text-white flex justify-between items-center">
          <div className="flex">
            {/* Back navigation button */}
            <button
              onClick={handleBack}
              className="px-3 py-3 text-gray-300 hover:text-white hover:bg-slate-700 transition-colors"
            >
              <ChevronLeft size={24} strokeWidth={3} />
            </button>
            {/* Tab buttons */}
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-3 text-xs font-bold transition-colors border-t-4 ${activeTab === tab.id
                  ? 'bg-white border-secondary text-primary'
                  : 'border-primary text-white hover:bg-secondary hover:border-secondary'
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          {/* User assignment section */}
          <div className="flex items-center gap-2 px-4">
            <span className="text-xs text-white">Users Assigned:</span>
            <div className="flex items-center">
              {/* User avatars */}
              <div className="flex -space-x-2">
                <div className="w-6 h-6 rounded-full bg-gray-400"></div>
                <div className="w-6 h-6 rounded-full bg-blue-500"></div>
                <div className="w-6 h-6 rounded-full bg-red-500"></div>
                <div className="w-6 h-6 rounded-full bg-purple-900 items-center justify-center flex text-xs">+1</div>
              </div>
              {/* Add user button */}
              <button className="ml-2 w-6 h-6 rounded-full bg-secondary text-white flex items-center justify-center text-lg hover:bg-primary">
                +
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1">{renderTabContent()}</div>

      {/* Bottom action bar */}
      <div className="border-t bg-white px-4 py-3 flex justify-center items-center gap-4">
        <button className="px-4 py-2 rounded-full font-bold text-[10px] uppercase transition-colors border border-secondary bg-white text-secondary hover:bg-secondary/25 hover:border-secondary/25">
          Export Draft
        </button>
        <button
          onClick={handleSubmitReview}
          className="px-4 py-2 rounded-full font-bold text-[10px] uppercase transition-colors bg-secondary text-white hover:bg-blue-700 disabled:bg-secondary/25"
          disabled={response.progress !== 100}
        >
          Submit for Review
        </button>
      </div>

      {/* Review submission modal */}
      {showReviewModal && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 bg-white border border-gray-300 shadow-lg rounded-lg px-6 py-4 z-50">
          <p className="text-sm text-gray-700">{reviewMessage}</p>
        </div>
      )}

    </section>
  );
}