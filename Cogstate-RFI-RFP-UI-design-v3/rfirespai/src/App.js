// App.jsx
// Ensure you have Tailwind CSS set up in your project.
// You would typically install lucide-react: npm install lucide-react

import React, { useState, useEffect } from 'react';
import {
    LayoutDashboard, Library, FileText, Users, Settings, UserCircle, Search, Plus, Eye, Save,
    CheckCircle, ChevronDown, UploadCloud, Paperclip, Trash2, MessageSquare, ArrowLeft, ArrowRight,
    Bold, Italic, Underline, List, ListOrdered, Link as LinkIcon, Table, Sparkles, Loader2, GitCompareArrows, XCircle, Edit, FileUp
} from 'lucide-react';

// Mock User Data
const currentUser = {
    name: 'RFP_Coordinator',
    avatarUrl: 'https://placehold.co/40x40/E0E0E0/B0B0B0?text=RC' // Placeholder avatar
};

const initialRfpProjects = [
    {
        id: 'proj1',
        title: "Billye Pharmaceuticals RFI",
        status: "In Progress",
        lastUpdated: "2025-07-10T17:00:00Z",
        section: "Section 2: Technical Capabilities",
        progress: 45,
        questions: [
            // Section 1: Corporate Overview
            { id: 'q1', text: "1.1 Please provide your company's legal name, primary address, and main contact information.", status: "Not Started", assignedTo: null, response: "" },
            { id: 'q2', text: "1.2 State the total number of full-time employees and list the number of specialists in key areas (e.g., Neurology, Cardiology, Oncology).", status: "Not Started", assignedTo: null, response: "" },
            // Section 2: Service Offerings
            { id: 'q3', text: "2.1 Provide a comprehensive list of the clinical trial services you offer.", status: "Not Started", assignedTo: null, response: "" },
            { id: 'q4', text: "2.2 Describe your data management systems, including compliance with 21 CFR Part 11 and GDPR.", status: "In Progress", assignedTo: "DM_Lead", response: "Our primary data management system is 'ClinicalVault X', a 21 CFR Part 11 compliant platform offering robust data capture, validation, and reporting features. It integrates seamlessly with EDC and other critical trial systems." },
            // Section 3: Cognitive Assessment Capabilities
            { id: 'q5', text: "3.1 Describe your experience with cognitive and CNS assessments in clinical trials. Please list the specific validated cognitive batteries you are proficient in (e.g., Cogstate, CANTAB, ADAS-Cog).", status: "Not Started", assignedTo: "CR_Head", response: "" },
            { id: 'q6', text: "3.2 What is your process for training and certifying raters who administer cognitive assessments to ensure inter-rater reliability?", status: "Not Started", assignedTo: "CR_Head", response: "" },
            { id: 'q7', text: "3.3 Explain your capabilities for digital and remote cognitive data collection. What platforms do you support?", status: "Not Started", assignedTo: null, response: "" },
            { id: 'q8', text: "3.4 How do you manage placebo and learning effects in cognitive trials? Describe your strategies and any specialized training provided to staff and subjects.", status: "Not Started", assignedTo: null, response: "" },
            { id: 'q9', text: "3.5 Detail your quality assurance processes for cognitive data.", status: "Not Started", assignedTo: null, response: "" },
        ]
    },
    {
        id: 'proj2',
        title: "BioVentures Cardiology RFP",
        status: "In Review",
        lastUpdated: "2025-07-09T11:30:00Z",
        section: "Section 4: Budget Proposal",
        progress: 90,
        questions: [
           // Section 1: Corporate Overview
           { id: 'q1', text: "1.1 Please provide your company's legal name, primary address, and main contact information.", status: "Not Started", assignedTo: null, response: "" },
           { id: 'q2', text: "1.2 State the total number of full-time employees and list the number of specialists in key areas (e.g., Neurology, Cardiology, Oncology).", status: "Not Started", assignedTo: null, response: "" },
           // Section 2: Service Offerings
           { id: 'q3', text: "2.1 Provide a comprehensive list of the clinical trial services you offer.", status: "Not Started", assignedTo: null, response: "" },
           { id: 'q4', text: "2.2 Describe your data management systems, including compliance with 21 CFR Part 11 and GDPR.", status: "In Progress", assignedTo: "DM_Lead", response: "Our primary data management system is 'ClinicalVault X', a 21 CFR Part 11 compliant platform offering robust data capture, validation, and reporting features. It integrates seamlessly with EDC and other critical trial systems." },
           // Section 3: Cognitive Assessment Capabilities
           { id: 'q5', text: "3.1 Describe your experience with cognitive and CNS assessments in clinical trials. Please list the specific validated cognitive batteries you are proficient in (e.g., Cogstate, CANTAB, ADAS-Cog).", status: "Not Started", assignedTo: "CR_Head", response: "" },
           { id: 'q6', text: "3.2 What is your process for training and certifying raters who administer cognitive assessments to ensure inter-rater reliability?", status: "Not Started", assignedTo: "CR_Head", response: "" },
           { id: 'q7', text: "3.3 Explain your capabilities for digital and remote cognitive data collection. What platforms do you support?", status: "Not Started", assignedTo: null, response: "" },
           { id: 'q8', text: "3.4 How do you manage placebo and learning effects in cognitive trials? Describe your strategies and any specialized training provided to staff and subjects.", status: "Not Started", assignedTo: null, response: "" },
           { id: 'q9', text: "3.5 Detail your quality assurance processes for cognitive data.", status: "Not Started", assignedTo: null, response: "" },         
        ]
    },
    {
        id: 'proj3',
        title: "NeuroGen CNS Study RFI",
        status: "Submitted",
        lastUpdated: "2025-07-05T15:45:00Z",
        section: "Section 1: Corporate Overview",
        progress: 100,
        questions: [
                     // Section 1: Corporate Overview
                     { id: 'q1', text: "1.1 Please provide your company's legal name, primary address, and main contact information.", status: "Not Started", assignedTo: null, response: "" },
                     { id: 'q2', text: "1.2 State the total number of full-time employees and list the number of specialists in key areas (e.g., Neurology, Cardiology, Oncology).", status: "Not Started", assignedTo: null, response: "" },
                     // Section 2: Service Offerings
                     { id: 'q3', text: "2.1 Provide a comprehensive list of the clinical trial services you offer.", status: "Not Started", assignedTo: null, response: "" },
                     { id: 'q4', text: "2.2 Describe your data management systems, including compliance with 21 CFR Part 11 and GDPR.", status: "In Progress", assignedTo: "DM_Lead", response: "Our primary data management system is 'ClinicalVault X', a 21 CFR Part 11 compliant platform offering robust data capture, validation, and reporting features. It integrates seamlessly with EDC and other critical trial systems." },
                     // Section 3: Cognitive Assessment Capabilities
                     { id: 'q5', text: "3.1 Describe your experience with cognitive and CNS assessments in clinical trials. Please list the specific validated cognitive batteries you are proficient in (e.g., Cogstate, CANTAB, ADAS-Cog).", status: "Not Started", assignedTo: "CR_Head", response: "" },
                     { id: 'q6', text: "3.2 What is your process for training and certifying raters who administer cognitive assessments to ensure inter-rater reliability?", status: "Not Started", assignedTo: "CR_Head", response: "" },
                     { id: 'q7', text: "3.3 Explain your capabilities for digital and remote cognitive data collection. What platforms do you support?", status: "Not Started", assignedTo: null, response: "" },
                     { id: 'q8', text: "3.4 How do you manage placebo and learning effects in cognitive trials? Describe your strategies and any specialized training provided to staff and subjects.", status: "Not Started", assignedTo: null, response: "" },
                     { id: 'q9', text: "3.5 Detail your quality assurance processes for cognitive data.", status: "Not Started", assignedTo: null, response: "" },
           
        ]
    }
];


const knowledgeBaseSuggestions = [
    { id: 'kb1', title: "SOP-005: Data Management System Overview", category: "SOPs", snippet: "Our validated system ClinicalVault X provides comprehensive data management...", fullText: "Our primary data management system is 'ClinicalVault X', a fully validated platform offering robust data capture, validation, and reporting features. It integrates seamlessly with EDC and other critical trial systems, ensuring data integrity from collection to submission." },
    { id: 'kb2', title: "Past Response: ClientABC RFI - Q.3.4 (Data Systems)", category: "Past Responses", snippet: "We utilize a tiered data storage solution with regular backups...", fullText: "We utilize a tiered data storage solution with regular backups and disaster recovery protocols. Our systems are compliant with 21 CFR Part 11. All data is managed within our US-based data centers." },
    { id: 'kb3', title: "Fact: Patient Recruitment Success Metrics", category: "Organizational Facts", snippet: "Achieved 95% of recruitment targets for rare disease studies in the past year.", fullText: "In the last fiscal year, our organization successfully achieved 95% of its patient recruitment targets across all rare disease studies, demonstrating our strong network and effective outreach strategies." },
];

const auditTrailData = [
    { id: 'at1', timestamp: '2025-07-10T23:20:00Z', actor: 'AI (Gemini)', action: 'Generated initial draft for question 2.1.', questionId: 'q1', type: 'AI' },
    { id: 'at2', timestamp: '2025-07-10T23:35:12Z', actor: 'DM_Lead', action: 'Edited response for question 2.1.', questionId: 'q1', type: 'EDIT' },
    { id: 'at3', timestamp: '2025-07-11T00:02:45Z', actor: 'CR_Head', action: 'Marked question 2.3 as complete.', questionId: 'q3', type: 'COMPLETE' },
    { id: 'at4', timestamp: '2025-07-11T01:10:05Z', actor: 'Safety_Officer', action: 'Edited response for question 2.4.', questionId: 'q4', type: 'EDIT' },
    { id: 'at5', timestamp: '2025-07-11T01:15:21Z', actor: 'Safety_Officer', action: 'Marked question 2.4 as complete.', questionId: 'q4', type: 'COMPLETE' },
    { id: 'at6', timestamp: '2025-07-11T01:30:00Z', actor: 'AI (Gemini)', action: 'Generated initial draft for question 2.2.', questionId: 'q2', type: 'AI' },
].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)); // Sort descending

// Helper component for Rich Text Editor (Placeholder)
const RichTextEditorPlaceholder = ({ value, onChange, placeholder, disabled = false }) => (
    <textarea
        className="w-full h-32 p-2 border border-gray-300 rounded-md focus:ring-teal-500 focus:border-teal-500 transition-shadow disabled:bg-gray-100"
        value={value}
        onChange={onChange}
        placeholder={placeholder || "Enter details here..."}
        disabled={disabled}
    />
);

// Header Component
const Header = ({ setCurrentView }) => {
    const navItems = [
        { name: 'Dashboard', view: 'DASHBOARD', icon: <LayoutDashboard size={18} /> },
        { name: 'RFI/RFP Responses', view: 'INGRESS', icon: <FileText size={18} /> },
        { name: 'Knowledge Base', view: 'KNOWLEDGE_BASE_LIST', icon: <Library size={18} /> },
        { name: 'Admin', view: 'ADMIN', icon: <Settings size={18} /> },
    ];

    return (
        <header className="bg-slate-800 text-white shadow-md sticky top-0 z-50">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    {/* Placeholder for Logo */}
                    <div className="text-xl font-bold text-teal-400">Cogstate RFI Response with AI</div>
                    <nav className="flex space-x-1">
                        {navItems.map(item => (
                            <button
                                key={item.view}
                                onClick={() => setCurrentView(item.view)}
                                className="flex items-center space-x-2 px-3 py-2 rounded-md hover:bg-slate-700 transition-colors text-sm"
                                aria-label={item.name}
                            >
                                {item.icon}
                                <span>{item.name}</span>
                            </button>
                        ))}
                    </nav>
                </div>
                <div className="flex items-center space-x-3">
                    <UserCircle size={24} />
                    <span className="text-sm">{currentUser.name}</span>
                </div>
            </div>
        </header>
    );
};

// Knowledge Base Input View (Wireframe 1)
const KnowledgeBaseInputView = ({ setCurrentView }) => {
    const [entryType, setEntryType] = useState('SERVICE');
    const [serviceName, setServiceName] = useState('');
    const [serviceCategory, setServiceCategory] = useState('');
    const [detailedDescription, setDetailedDescription] = useState('');
    const [tags, setTags] = useState('');
    const [attachments, setAttachments] = useState([]);

    const [isSuggestingTags, setIsSuggestingTags] = useState(false);
    const [tagSuggestionError, setTagSuggestionError] = useState(null);

    const handleFileUpload = (event) => {
        const files = Array.from(event.target.files);
        setAttachments(prev => [...prev, ...files.map(f => ({ name: f.name, id: Math.random().toString(36).substring(7) }))]);
    };

    const removeAttachment = (id) => {
        setAttachments(prev => prev.filter(att => att.id !== id));
    };

    const handleSuggestTags = async () => {
        if (!detailedDescription) {
            setTagSuggestionError("Please provide a detailed description first.");
            return;
        }
        setIsSuggestingTags(true);
        setTagSuggestionError(null);
        setTags(''); // Clear previous tags or indicate loading

        const prompt = `Based on the following service description for a clinical trial organization, suggest 5-7 relevant comma-separated keywords or tags. These tags will be used for a knowledge base to categorize and find this service. Output only the comma-separated tags, with no introductory text or labels. For example: tag1, tag2, tag3. Description: "${detailedDescription}"`;

        try {
            let chatHistory = [{ role: "user", parts: [{ text: prompt }] }];
            const payload = { contents: chatHistory };
            const apiKey = ""; // Handled by Canvas environment
            const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`;

            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error("Gemini API Error (Suggest Tags):", errorData);
                throw new Error(`API request failed with status ${response.status}: ${errorData?.error?.message || 'Unknown error'}`);
            }

            const result = await response.json();

            if (result.candidates && result.candidates.length > 0 &&
                result.candidates[0].content && result.candidates[0].content.parts &&
                result.candidates[0].content.parts.length > 0) {
                const suggestedTags = result.candidates[0].content.parts[0].text;
                setTags(suggestedTags.trim());
            } else {
                console.error("Unexpected API response structure (Suggest Tags):", result);
                throw new Error("Failed to parse suggested tags from API.");
            }
        } catch (error) {
            console.error("Error suggesting tags:", error);
            setTagSuggestionError(error.message || "An unexpected error occurred while suggesting tags.");
            setTags("Error suggesting tags.");
        } finally {
            setIsSuggestingTags(false);
        }
    };


    return (
        <div className="p-6 bg-gray-50 min-h-screen">
            <div className="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow-lg">
                <h1 className="text-2xl font-semibold text-gray-800 mb-2">Knowledge Base</h1>
                <p className="text-sm text-teal-600 mb-6 font-medium">KNOWLEDGE BASE &gt; Add New Entry</p>

                <form onSubmit={(e) => e.preventDefault()}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                        <div>
                            <label htmlFor="entryType" className="block text-sm font-medium text-gray-700 mb-1">Entry Type</label>
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
  <option value="service">Service</option> {/* Note: capital 'S' */}
  <option value="sop">SOP</option>
  <option value="policy">Policy</option>
  <option value="past_response">Past Response</option>
</select>
                        </div>
                    </div>

                    {entryType === 'SERVICE' && (
                        <>
                            <div className="mb-6">
                                <label htmlFor="serviceName" className="block text-sm font-medium text-gray-700 mb-1">Service Name</label>
                                <input
                                    type="text"
                                    id="serviceName"
                                    value={serviceName}
                                    onChange={(e) => setServiceName(e.target.value)}
                                    placeholder="e.g., Phase III Clinical Trial Management"
                                    className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-teal-500 focus:border-teal-500"
                                />
                            </div>
                            <div className="mb-6">
                                <label htmlFor="serviceCategory" className="block text-sm font-medium text-gray-700 mb-1">Service Category</label>
                                <select
                                    id="serviceCategory"
                                    value={serviceCategory}
                                    onChange={(e) => setServiceCategory(e.target.value)}
                                    className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-teal-500 focus:border-teal-500"
                                >
                                    <option value="">Select Category...</option>
                                    <option value="clinical_Operations">Clinical Operations</option>
                                    <option value="data_Management">Data Management</option>
                                    <option value="regulatory_Affairs">Regulatory Affairs</option>
                                </select>
                            </div>
                        </>
                    )}

                    <div className="mb-6">
                        <label htmlFor="detailedDescription" className="block text-sm font-medium text-gray-700 mb-1">Detailed Description</label>
                        <RichTextEditorPlaceholder value={detailedDescription} onChange={(e) => setDetailedDescription(e.target.value)} />
                        <div className="mt-1 flex space-x-1 p-1 bg-gray-100 rounded-b-md border border-t-0 border-gray-300">
                            {[Bold, Italic, Underline, List, ListOrdered, LinkIcon, Table].map((Icon, idx) => (
                                <button key={idx} type="button" className="p-1.5 hover:bg-gray-200 rounded text-gray-600">
                                    <Icon size={16} />
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="mb-1">
                        <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-1">Tags (comma-separated)</label>
                        <div className="flex items-center space-x-2">
                            <input
                                type="text"
                                id="tags"
                                value={tags}
                                onChange={(e) => setTags(e.target.value)}
                                placeholder="e.g., oncology, global, patient safety"
                                className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-teal-500 focus:border-teal-500"
                                disabled={isSuggestingTags}
                            />
                            {entryType === 'SERVICE' && (
                                <button
                                    type="button"
                                    onClick={handleSuggestTags}
                                    disabled={isSuggestingTags || !detailedDescription}
                                    className="px-3 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 flex items-center"
                                >
                                    {isSuggestingTags ? <Loader2 size={18} className="animate-spin mr-2" /> : <Sparkles size={18} className="mr-2" />}
                                    Suggest Tags
                                </button>
                            )}
                        </div>
                         {tagSuggestionError && <p className="text-xs text-red-600 mt-1">{tagSuggestionError}</p>}
                    </div>


                    <div className="mb-6 mt-6"> {/* Added mt-6 for spacing */}
                        <label className="block text-sm font-medium text-gray-700 mb-1">Attachments</label>
                        <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                            <div className="space-y-1 text-center">
                                <UploadCloud className="mx-auto h-12 w-12 text-gray-400" />
                                <div className="flex text-sm text-gray-600">
                                    <label
                                        htmlFor="file-upload"
                                        className="relative cursor-pointer bg-white rounded-md font-medium text-teal-600 hover:text-teal-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-teal-500"
                                    >
                                        <span>Upload files</span>
                                        <input id="file-upload" name="file-upload" type="file" className="sr-only" multiple onChange={handleFileUpload} />
                                    </label>
                                    <p className="pl-1">or drag and drop</p>
                                </div>
                                <p className="text-xs text-gray-500">PNG, JPG, PDF up to 10MB</p>
                            </div>
                        </div>
                        {attachments.length > 0 && (
                            <div className="mt-3 space-y-2">
                                {attachments.map(file => (
                                    <div key={file.id} className="flex items-center justify-between p-2 border border-gray-200 rounded-md bg-gray-50">
                                        <div className="flex items-center space-x-2">
                                            <Paperclip size={16} className="text-gray-500" />
                                            <span className="text-sm text-gray-700">{file.name}</span>
                                        </div>
                                        <button type="button" onClick={() => removeAttachment(file.id)} className="text-red-500 hover:text-red-700">
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200 mt-8">
                        <button
                            type="button"
                            onClick={() => setCurrentView('KNOWLEDGE_BASE_LIST')}
                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500"
                        >
                            Cancel
                        </button>
                        <button
                            type="button"
                            className="px-4 py-2 text-sm font-medium text-teal-700 bg-teal-100 border border-transparent rounded-md shadow-sm hover:bg-teal-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500"
                        >
                            Save Draft
                        </button>
                        <button
                            type="submit"
                            className="px-4 py-2 text-sm font-medium text-white bg-teal-600 border border-transparent rounded-md shadow-sm hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500"
                        >
                            Submit for Approval
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

const AuditTrailView = ({ auditLog, questions }) => {
    
    const getIconForType = (type) => {
        switch (type) {
            case 'AI': return <Sparkles className="h-5 w-5 text-indigo-500" />;
            case 'EDIT': return <Edit className="h-5 w-5 text-yellow-500" />;
            case 'COMPLETE': return <CheckCircle className="h-5 w-5 text-green-500" />;
            default: return <FileText className="h-5 w-5 text-gray-500" />;
        }
    };
    
    const timeAgo = (date) => {
        const seconds = Math.floor((new Date() - new Date(date)) / 1000);
        let interval = seconds / 31536000;
        if (interval > 1) return Math.floor(interval) + " years ago";
        interval = seconds / 2592000;
        if (interval > 1) return Math.floor(interval) + " months ago";
        interval = seconds / 86400;
        if (interval > 1) return Math.floor(interval) + " days ago";
        interval = seconds / 3600;
        if (interval > 1) return Math.floor(interval) + " hours ago";
        interval = seconds / 60;
        if (interval > 1) return Math.floor(interval) + " minutes ago";
        return Math.floor(seconds) + " seconds ago";
    };

    return (
        <div className="bg-white p-6 rounded-lg shadow-md h-full overflow-y-auto">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Project Audit Trail</h3>
            <div className="flow-root">
                <ul role="list" className="-mb-8">
                    {auditLog.map((event, eventIdx) => {
                        const question = questions.find(q => q.id === event.questionId);
                        return (
                            <li key={event.id}>
                                <div className="relative pb-8">
                                    {eventIdx !== auditLog.length - 1 ? (
                                        <span className="absolute left-4 top-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true" />
                                    ) : null}
                                    <div className="relative flex space-x-3">
                                        <div>
                                            <span className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center ring-8 ring-white">
                                                {getIconForType(event.type)}
                                            </span>
                                        </div>
                                        <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                                            <div>
                                                <p className="text-sm text-gray-500">
                                                    <span className="font-medium text-gray-900">{event.actor}</span> {event.action}
                                                </p>
                                                {question && (
                                                    <p className="mt-1 text-xs text-gray-500 italic border-l-2 border-gray-200 pl-2">
                                                        Regarding: "{question.text}"
                                                    </p>
                                                )}
                                            </div>
                                            <div className="whitespace-nowrap text-right text-sm text-gray-500">
                                                <time dateTime={event.timestamp}>{timeAgo(event.timestamp)}</time>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </li>
                        );
                    })}
                </ul>
            </div>
        </div>
    );
};


// RFI/RFP Response Workspace View (Wireframe 2)
const RfpResponseWorkspaceView = ({ setCurrentView, project }) => {
    const [questions, setQuestions] = useState(project.questions);
    const [selectedQuestionId, setSelectedQuestionId] = useState(project.questions[0]?.id);
    const [currentResponse, setCurrentResponse] = useState(project.questions[0]?.response || '');
    const [kbSearchTerm, setKbSearchTerm] = useState('');
    const [activeTab, setActiveTab] = useState('Document Sections');

    const [isGeneratingResponse, setIsGeneratingResponse] = useState(false);
    const [generationError, setGenerationError] = useState(null);
    
    const [comparisonData, setComparisonData] = useState({ isLoading: false, error: null, data: null, sourceId: null, sourceTitle: null });

    const selectedQuestion = questions.find(q => q.id === selectedQuestionId);

    useEffect(() => {
        const newSelectedQuestion = questions.find(q => q.id === selectedQuestionId);
        setCurrentResponse(newSelectedQuestion?.response || '');
        setGenerationError(null); // Clear error when question changes
        setComparisonData({ isLoading: false, error: null, data: null, sourceId: null, sourceTitle: null }); // Clear comparison view
    }, [selectedQuestionId, questions]);

    const handleResponseChange = (e) => {
        setCurrentResponse(e.target.value);
    };

    const saveResponse = () => {
        setQuestions(prevQuestions =>
            prevQuestions.map(q =>
                q.id === selectedQuestionId ? { ...q, response: currentResponse, status: "In Progress" } : q
            )
        );
        alert("Response saved (mock)!");
    };
    
    const markAsComplete = () => {
         setQuestions(prevQuestions =>
            prevQuestions.map(q =>
                q.id === selectedQuestionId ? { ...q, response: currentResponse, status: "Completed" } : q
            )
        );
        alert("Marked as complete (mock)!");
    };

    const insertKbSnippet = (snippet) => {
        setCurrentResponse(prev => prev + (prev ? "\n\n" : "") + snippet); // Add snippet with spacing
    };

    const navigateQuestion = (direction) => {
        const currentIndex = questions.findIndex(q => q.id === selectedQuestionId);
        let nextIndex;
        if (direction === 'next') {
            nextIndex = Math.min(currentIndex + 1, questions.length - 1);
        } else {
            nextIndex = Math.max(currentIndex - 1, 0);
        }
        if (currentIndex !== nextIndex) {
            setSelectedQuestionId(questions[nextIndex].id);
        }
    };
    
    const getStatusColor = (status) => {
        switch (status) {
            case "In Progress": return "text-yellow-600 bg-yellow-100";
            case "Not Started": return "text-gray-600 bg-gray-100";
            case "Review Needed": return "text-blue-600 bg-blue-100";
            case "Completed": return "text-green-600 bg-green-100";
            default: return "text-gray-600 bg-gray-100";
        }
    };

    const handleGenerateDraftResponse = async () => {
        if (!selectedQuestion || !selectedQuestion.text) {
            setGenerationError("No question selected or question text is empty.");
            return;
        }

        setIsGeneratingResponse(true);
        setGenerationError(null);

        const prompt = `You are an expert in responding to RFIs and RFPs for a clinical trial organization. A client has asked the following question: "${selectedQuestion.text}". Please provide a comprehensive and professional draft response to this question. Focus on clarity, accuracy, and a helpful tone. If the question is about capabilities, highlight relevant strengths of a typical clinical trial organization. If the question is about processes, describe them clearly as a best practice. Avoid making up specific company names or highly proprietary details unless they are commonly known best practices. Generate a draft response:`;

        try {
            let chatHistory = [{ role: "user", parts: [{ text: prompt }] }];
            const payload = { contents: chatHistory };
            const apiKey = ""; // Handled by Canvas environment
            const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`;

            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) { throw new Error(`API request failed with status ${response.status}`); }

            const result = await response.json();

            if (result.candidates?.[0]?.content?.parts?.[0]?.text) {
                setCurrentResponse(result.candidates[0].content.parts[0].text);
            } else {
                throw new Error("Failed to parse generated response from API.");
            }
        } catch (error) {
            console.error("Error generating draft response:", error);
            setGenerationError(error.message);
            setCurrentResponse("Failed to generate draft. Please try again or write manually.");
        } finally {
            setIsGeneratingResponse(false);
        }
    };

    const handleCompareResponse = async (pastResponse) => {
        if (!selectedQuestion || !selectedQuestion.text) {
            setComparisonData({ isLoading: false, error: "Select a question first.", data: null, sourceId: null, sourceTitle: null });
            return;
        }
        
        setComparisonData({ isLoading: true, error: null, data: null, sourceId: pastResponse.id, sourceTitle: pastResponse.title });

        const prompt = `You are an RFI/RFP analysis expert. Your task is to compare a past response to a new RFI question and break down the past response into segments, highlighting their relevance.

Current RFI Question: "${selectedQuestion.text}"

Past Response Text: "${pastResponse.fullText}"

Analyze the "Past Response Text" and segment it based on its relevance to the "Current RFI Question". For each segment, classify it as 'same', 'similar', or 'different'.
- 'same': The content directly answers a part of the current question and is highly reusable.
- 'similar': The content is related but may need updates. For example, it answers a part of the question but is missing a key detail mentioned in the current question (like GDPR), or it's a good starting point but needs tailoring.
- 'different': The content is not relevant to the current question.

Return a JSON object with a single key "analysis" which is an array of objects. Each object in the array must have two keys: "type" (string, one of 'same', 'similar', 'different') and "text" (string, the segment of text). The segments must cover the entire "Past Response Text" without omissions.
`;

        const payload = {
            contents: [{ role: "user", parts: [{ text: prompt }] }],
            generationConfig: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: "OBJECT",
                    properties: {
                        "analysis": {
                            type: "ARRAY",
                            items: {
                                type: "OBJECT",
                                properties: {
                                    "type": { "type": "STRING" },
                                    "text": { "type": "STRING" }
                                },
                                required: ["type", "text"]
                            }
                        }
                    }
                }
            }
        };

        try {
            const apiKey = ""; // Handled by Canvas environment
            const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`;
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) { throw new Error(`API request failed with status ${response.status}`); }
            
            const result = await response.json();

            if (result.candidates?.[0]?.content?.parts?.[0]?.text) {
                const parsedJson = JSON.parse(result.candidates[0].content.parts[0].text);
                setComparisonData(prev => ({ ...prev, isLoading: false, data: parsedJson.analysis }));
            } else {
                throw new Error("Failed to parse comparison from API.");
            }
        } catch (error) {
            console.error("Error comparing response:", error);
            setComparisonData(prev => ({ ...prev, isLoading: false, error: error.message }));
        }
    };
    
    const getHighlightClass = (type) => {
        switch (type) {
            case 'same': return 'bg-green-100 text-green-800';
            case 'similar': return 'bg-yellow-100 text-yellow-800';
            case 'different': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const tabs = ['Document Sections', 'Team Chat', 'Knowledge Search', 'Audit Trail'];

    return (
        <div className="flex flex-col h-[calc(100vh-4rem)]">
            {/* Context & Tabs */}
            <div className="bg-gray-100 p-3 border-b border-gray-300">
                <div className="container mx-auto px-4">
                    <p className="text-sm text-gray-600">
                        <button onClick={() => setCurrentView('INGRESS')} className="hover:underline text-teal-600">RFI/RFP RESPONSES</button> &gt; Project: <span className="font-semibold text-gray-800">{project.title}</span>
                    </p>
                    <h2 className="text-xl font-semibold text-teal-700">{project.section}</h2>
                </div>
            </div>
            <div className="bg-white border-b border-gray-200">
                <div className="container mx-auto px-4">
                    <nav className="flex space-x-4">
                        {tabs.map((tab) => (
                            <button 
                                key={tab} 
                                onClick={() => setActiveTab(tab)}
                                className={`py-3 px-1 border-b-2 ${activeTab === tab ? 'border-teal-500 text-teal-600 font-semibold' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} text-sm transition-colors`}
                            >
                                {tab}
                            </button>
                        ))}
                    </nav>
                </div>
            </div>

            {/* Main Workspace */}
            <div className="flex-grow container mx-auto px-4 py-4 overflow-hidden">
                {activeTab === 'Document Sections' && (
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-6 h-full">
                        {/* Left Panel */}
                        <div className="md:col-span-5 lg:col-span-4 bg-white p-4 rounded-lg shadow-md overflow-y-auto">
                            <h3 className="text-lg font-semibold text-gray-800 mb-3">Client Questions</h3>
                            <div className="space-y-3">
                                {questions.map(q => (
                                    <div key={q.id} onClick={() => setSelectedQuestionId(q.id)} className={`p-3 rounded-md cursor-pointer transition-all ${selectedQuestionId === q.id ? 'bg-teal-50 ring-2 ring-teal-500 shadow-lg' : 'bg-gray-50 hover:bg-gray-100'}`}>
                                        <p className={`text-sm font-medium ${selectedQuestionId === q.id ? 'text-teal-700' : 'text-gray-700'}`}>{q.text}</p>
                                        <div className="mt-1.5 flex items-center justify-between text-xs">
                                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(q.status)}`}>{q.status}</span>
                                            <span className="text-gray-500">{q.assignedTo || 'Unassigned'}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Right Panel */}
                        <div className="md:col-span-7 lg:col-span-8 bg-white p-4 rounded-lg shadow-md flex flex-col overflow-y-auto">
                            {selectedQuestion ? (
                                <>
                                    <div className="flex justify-between items-center mb-3">
                                        <h3 className="text-lg font-semibold text-gray-800">Response for: <span className="text-teal-600">{selectedQuestion.text.substring(0,40)+'...'}</span></h3>
                                        <div className="flex space-x-2">
                                            <button onClick={() => navigateQuestion('prev')} className="p-1.5 rounded-md hover:bg-gray-100 text-gray-500 disabled:text-gray-300" disabled={questions.findIndex(q => q.id === selectedQuestionId) === 0} aria-label="Previous question"><ArrowLeft size={20}/></button>
                                            <button onClick={() => navigateQuestion('next')} className="p-1.5 rounded-md hover:bg-gray-100 text-gray-500 disabled:text-gray-300" disabled={questions.findIndex(q => q.id === selectedQuestionId) === questions.length - 1} aria-label="Next question"><ArrowRight size={20}/></button>
                                        </div>
                                    </div>
                                    
                                    <div className="mb-4 flex-grow">
                                        <RichTextEditorPlaceholder value={currentResponse} onChange={handleResponseChange} placeholder={isGeneratingResponse ? "✨ Generating draft response..." : "Draft your response here..."} disabled={isGeneratingResponse} />
                                        <div className="mt-1 flex space-x-1 p-1 bg-gray-100 rounded-b-md border border-t-0 border-gray-200">
                                            {[Bold, Italic, Underline, List, ListOrdered, LinkIcon, Table].map((Icon, idx) => (<button key={idx} type="button" className="p-1.5 hover:bg-gray-200 rounded text-gray-600"><Icon size={16} /></button>))}
                                        </div>
                                        {generationError && <p className="text-xs text-red-600 mt-1">{generationError}</p>}
                                    </div>

                                    <div className="flex items-center space-x-2 mb-4">
                                        <button onClick={handleGenerateDraftResponse} disabled={isGeneratingResponse || !selectedQuestion} className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400 flex items-center space-x-1.5">
                                            {isGeneratingResponse ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}<span>Generate Draft</span>
                                        </button>
                                        <button onClick={saveResponse} disabled={isGeneratingResponse} className="px-4 py-2 text-sm font-medium text-white bg-teal-600 rounded-md hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 flex items-center space-x-1.5 disabled:bg-gray-400"><Save size={16} /><span>Save Section</span></button>
                                        <button onClick={markAsComplete} disabled={isGeneratingResponse} className="px-4 py-2 text-sm font-medium text-teal-700 bg-teal-100 rounded-md hover:bg-teal-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 flex items-center space-x-1.5 disabled:bg-gray-300 disabled:text-gray-500"><CheckCircle size={16} /><span>Mark as Complete</span></button>
                                    </div>

                                    <div className="border-t border-gray-200 pt-4">
                                        <h4 className="text-md font-semibold text-gray-700 mb-2">Knowledge Base Suggestions</h4>
                                        <div className="relative mb-3">
                                            <input type="text" placeholder="Search Knowledge Base..." value={kbSearchTerm} onChange={(e) => setKbSearchTerm(e.target.value)} className="w-full p-2 pl-10 border border-gray-300 rounded-md focus:ring-teal-500 focus:border-teal-500" />
                                            <Search size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                                        </div>
                                        <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                                            {knowledgeBaseSuggestions.filter(s => s.title.toLowerCase().includes(kbSearchTerm.toLowerCase()) || s.snippet.toLowerCase().includes(kbSearchTerm.toLowerCase())).map(suggestion => (
                                                <div key={suggestion.id} className="p-3 bg-gray-50 rounded-md border border-gray-200 hover:shadow-sm transition-shadow">
                                                    <h5 className="text-sm font-semibold text-teal-700">{suggestion.title} <span className="text-xs text-gray-500 font-normal">({suggestion.category})</span></h5>
                                                    <p className="text-xs text-gray-600 mt-0.5 mb-1.5">{suggestion.snippet}</p>
                                                    <div className="flex space-x-2">
                                                        <button onClick={() => insertKbSnippet(suggestion.fullText)} className="text-xs px-2 py-1 bg-teal-100 text-teal-700 rounded hover:bg-teal-200 transition-colors flex items-center space-x-1"><Plus size={14}/><span>Insert</span></button>
                                                        <button onClick={() => handleCompareResponse(suggestion)} disabled={comparisonData.isLoading && comparisonData.sourceId === suggestion.id} className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors flex items-center space-x-1 disabled:bg-gray-300"><GitCompareArrows size={14}/><span>Compare</span></button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                        
                                        {comparisonData.sourceId && (
                                            <div className="mt-4 p-4 border border-gray-300 rounded-lg bg-white shadow-inner">
                                                <div className="flex justify-between items-center mb-3">
                                                    <div>
                                                        <h5 className="font-semibold text-gray-800">Comparison Analysis</h5>
                                                        <p className="text-xs text-gray-500">Comparing with: "{comparisonData.sourceTitle}"</p>
                                                    </div>
                                                    <button onClick={() => setComparisonData({ isLoading: false, error: null, data: null, sourceId: null, sourceTitle: null })} className="text-gray-500 hover:text-gray-800"><XCircle size={20}/></button>
                                                </div>
                                                {comparisonData.isLoading && <div className="flex items-center justify-center p-4"><Loader2 className="animate-spin text-teal-600" size={24} /> <span className="ml-2">Analyzing...</span></div>}
                                                {comparisonData.error && <div className="p-3 bg-red-100 text-red-700 text-sm rounded-md">Error: {comparisonData.error}</div>}
                                                {comparisonData.data && (
                                                    <div>
                                                        <div className="text-sm p-3 border rounded-md leading-relaxed">
                                                            {comparisonData.data.map((segment, index) => (
                                                                <span key={index} className={`px-1 py-0.5 rounded-sm ${getHighlightClass(segment.type)}`}>{segment.text}</span>
                                                            ))}
                                                        </div>
                                                        <div className="flex space-x-4 text-xs mt-3">
                                                            <div className="flex items-center"><span className="w-3 h-3 rounded-full bg-green-200 mr-1.5"></span>Same</div>
                                                            <div className="flex items-center"><span className="w-3 h-3 rounded-full bg-yellow-200 mr-1.5"></span>Similar</div>
                                                            <div className="flex items-center"><span className="w-3 h-3 rounded-full bg-red-200 mr-1.5"></span>Different</div>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </>
                            ) : (
                                <p className="text-gray-500">Select a question to view details and respond.</p>
                            )}
                        </div>
                    </div>
                )}
                {activeTab === 'Audit Trail' && (
                    <AuditTrailView auditLog={auditTrailData} questions={project.questions} />
                )}
                 {activeTab === 'Team Chat' && (
                    <div className="bg-white p-6 rounded-lg shadow-md h-full">
                        <h3 className="text-xl font-semibold text-gray-800 mb-4">Team Chat</h3>
                        <p className="text-gray-500">Team chat feature coming soon.</p>
                    </div>
                )}
                {activeTab === 'Knowledge Search' && (
                     <div className="bg-white p-6 rounded-lg shadow-md h-full">
                        <h3 className="text-xl font-semibold text-gray-800 mb-4">Knowledge Search</h3>
                        <p className="text-gray-500">Advanced knowledge base search feature coming soon.</p>
                    </div>
                )}
            </div>

            {/* Bottom Bar */}
            <footer className="bg-gray-100 p-3 border-t border-gray-200">
                <div className="container mx-auto px-4 flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-sm text-gray-700">
                        <span>Progress: {project.progress}%</span>
                        <div className="w-32 h-2 bg-gray-300 rounded-full overflow-hidden"><div className="h-full bg-teal-500" style={{ width: `${project.progress}%` }}></div></div>
                    </div>
                    <span className="text-sm text-gray-600">Due Date: {project.dueDate}</span>
                    <div className="space-x-2">
                        <button className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50">Export Draft</button>
                        <button className="px-3 py-1.5 text-xs font-medium text-white bg-teal-600 rounded-md shadow-sm hover:bg-teal-700">Submit for Review</button>
                    </div>
                </div>
            </footer>
        </div>
    );
};

const IngressView = ({ setCurrentView, setSelectedProject }) => {
    const [projects, setProjects] = useState(initialRfpProjects);
    const [uploadingFile, setUploadingFile] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setUploadingFile(e.target.files[0]);
        }
    };

    const handleUpload = () => {
        if (!uploadingFile) return;
        setIsProcessing(true);
        // Simulate processing and breaking into sections
        setTimeout(() => {
            const newProject = {
                id: `proj${projects.length + 1}`,
                title: uploadingFile.name.replace(/\.[^/.]+$/, ""), // Use filename as title
                status: "In Progress",
                lastUpdated: new Date().toISOString(),
                section: "Section 1: Initial Sections",
                progress: 5,
                questions: [{ id: 'new_q1', text: "1.1 Please provide a company overview.", status: "Not Started", assignedTo: null, response: "" }]
            };
            setProjects(prev => [newProject, ...prev]);
            setIsProcessing(false);
            setUploadingFile(null);
        }, 2500);
    };

    const getStatusClass = (status) => {
        switch (status) {
            case "In Progress": return "bg-blue-100 text-blue-800";
            case "In Review": return "bg-yellow-100 text-yellow-800";
            case "Ready to Submit": return "bg-purple-100 text-purple-800";
            case "Submitted": return "bg-green-100 text-green-800";
            default: return "bg-gray-100 text-gray-800";
        }
    };

    const timeAgo = (date) => {
        const seconds = Math.floor((new Date() - new Date(date)) / 1000);
        let interval = seconds / 31536000;
        if (interval > 1) return Math.floor(interval) + " years ago";
        interval = seconds / 2592000;
        if (interval > 1) return Math.floor(interval) + " months ago";
        interval = seconds / 86400;
        if (interval > 1) return Math.floor(interval) + " days ago";
        interval = seconds / 3600;
        if (interval > 1) return Math.floor(interval) + " hours ago";
        interval = seconds / 60;
        if (interval > 1) return Math.floor(interval) + " minutes ago";
        return Math.floor(seconds) + " seconds ago";
    };

    return (
        <div className="p-6 bg-gray-50 min-h-screen">
            <div className="container mx-auto">
                <div className="bg-white p-8 rounded-lg shadow-lg mb-8">
                    <h2 className="text-xl font-semibold text-gray-800 mb-4">Ingest New RFI/RFP Request</h2>
                    <div className="flex items-center space-x-4">
                        <label htmlFor="rfi-upload" className="flex-1 p-4 border-2 border-dashed border-gray-300 rounded-md cursor-pointer hover:border-teal-500 hover:bg-gray-50 text-center">
                            <FileUp className="mx-auto h-10 w-10 text-gray-400 mb-2" />
                            <span className="text-sm text-gray-600">{uploadingFile ? uploadingFile.name : 'Click to select a file or drag and drop'}</span>
                            <input id="rfi-upload" type="file" className="sr-only" onChange={handleFileChange} />
                        </label>
                        <button
                            onClick={handleUpload}
                            disabled={!uploadingFile || isProcessing}
                            className="px-6 py-4 text-sm font-medium text-white bg-teal-600 rounded-md shadow-sm hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 disabled:bg-gray-400 flex items-center"
                        >
                            {isProcessing ? <Loader2 className="animate-spin mr-2" /> : <UploadCloud className="mr-2" />}
                            {isProcessing ? 'Processing...' : 'Upload & Process'}
                        </button>
                    </div>
                </div>

                <div>
                    <h2 className="text-2xl font-semibold text-gray-800 mb-6">Active RFI/RFP Projects</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {projects.map(project => (
                            <div key={project.id} className="bg-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow cursor-pointer" onClick={() => { setSelectedProject(project); setCurrentView('RFP_WORKSPACE'); }}>
                                <div className="flex justify-between items-start mb-2">
                                    <h3 className="text-lg font-bold text-gray-800">{project.title}</h3>
                                    <span className={`px-2.5 py-0.5 text-xs font-medium rounded-full ${getStatusClass(project.status)}`}>
                                        {project.status}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-500">Last updated: {timeAgo(project.lastUpdated)}</p>
                                <div className="w-full bg-gray-200 rounded-full h-2 mt-4">
                                    <div className="bg-teal-500 h-2 rounded-full" style={{ width: `${project.progress}%` }}></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

// Placeholder Views
const PlaceholderView = ({ title, setCurrentView, showAddButton = false, addTargetView = null }) => (
    <div className="p-6 bg-gray-50 min-h-screen">
        <div className="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow-lg">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-semibold text-gray-800">{title}</h1>
                {showAddButton && addTargetView && (
                     <button onClick={() => setCurrentView(addTargetView)} className="px-4 py-2 text-sm font-medium text-white bg-teal-600 rounded-md shadow-sm hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 flex items-center space-x-2"><Plus size={18} /><span>Add New Entry</span></button>
                )}
            </div>
            <p className="text-gray-600">Content for {title} will be displayed here. This is a placeholder.</p>
            {title === "Knowledge Base" && (<div className="mt-4"><p className="text-sm text-gray-500">Example actions:</p><ul className="list-disc list-inside text-sm text-gray-600"><li>View existing knowledge articles</li><li>Filter by category, tags</li><li>Search articles</li></ul></div>)}
             {title === "RFI/RFP Responses" && (<div className="mt-4"><p className="text-sm text-gray-500">Example actions:</p><ul className="list-disc list-inside text-sm text-gray-600"><li>List all active and past RFIs/RFPs</li><li>Start a new RFI/RFP response project</li><li>View status of ongoing responses</li></ul><button onClick={() => setCurrentView('RFP_WORKSPACE')} className="mt-4 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">Go to Example RFP Workspace</button></div>)}
        </div>
    </div>
);


// Main App Component
export default function App() {
    const [currentView, setCurrentView] = useState('INGRESS'); // Default view
    const [selectedProject, setSelectedProject] = useState(initialRfpProjects[0]);

    let viewComponent;
    switch (currentView) {
        case 'DASHBOARD':
            viewComponent = <PlaceholderView title="Dashboard" setCurrentView={setCurrentView} />;
            break;
        case 'INGRESS':
            viewComponent = <IngressView setCurrentView={setCurrentView} setSelectedProject={setSelectedProject} />;
            break;
        case 'KNOWLEDGE_BASE_LIST':
            viewComponent = <PlaceholderView title="Knowledge Base" setCurrentView={setCurrentView} showAddButton={true} addTargetView="KNOWLEDGE_BASE_ADD_NEW" />;
            break;
        case 'KNOWLEDGE_BASE_ADD_NEW':
            viewComponent = <KnowledgeBaseInputView setCurrentView={setCurrentView} />;
            break;
        case 'RFP_WORKSPACE':
            viewComponent = <RfpResponseWorkspaceView setCurrentView={setCurrentView} project={selectedProject} />;
            break;
        case 'ADMIN':
            viewComponent = <PlaceholderView title="Admin Panel" setCurrentView={setCurrentView} />;
            break;
        default:
            viewComponent = <IngressView setCurrentView={setCurrentView} setSelectedProject={setSelectedProject} />;
    }

    return (
        <div className="min-h-screen bg-gray-100 font-sans">
            <Header setCurrentView={setCurrentView} />
            <main>
                {viewComponent}
            </main>
        </div>
    );
}

