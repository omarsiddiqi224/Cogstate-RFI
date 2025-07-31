import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { activeRFIList, getRFIDetails } from '../state/reducers/rfi';
import { useNavigate } from 'react-router-dom';
import FileUploader from '../components/FileUploader';

export default function RfiRfp() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { 
    activeProjects, 
    loading, 
    responseDetailsLoading 
  } = useSelector((state) => state.rfi);

  const timeAgo = (date) => {
    const seconds = Math.floor((new Date() - new Date(date)) / 1000);
    const intervals = [
      { label: "year", seconds: 31536000 },
      { label: "month", seconds: 2592000 },
      { label: "day", seconds: 86400 },
      { label: "hour", seconds: 3600 },
      { label: "minute", seconds: 60 },
      { label: "second", seconds: 1 },
    ];
    for (let i of intervals) {
      const count = Math.floor(seconds / i.seconds);
      if (count >= 1) return `${count} ${i.label}${count > 1 ? 's' : ''} ago`;
    }
    return "just now";
  };

  const getStatusConfig = (status) => {
    const statusMap = {
      'REVIEW_READY': { text: 'Ready for review', bg: 'bg-white', textColor: 'text-gray-800', border: 'border-gray-300' },
      'NOT_STARTED': { text: 'Not started', bg: 'bg-[#f3f8fb]', textColor: 'text-[#475d7c]', border: 'border-[#f3f8fb]' },
      'IN_PROGRESS': { text: 'In progress', bg: 'bg-[#f6e6f3]', textColor: 'text-[#9e007e]', border: 'border-[#f6e6f3]' },
      'IN_REVIEW': { text: 'In review', bg: 'bg-[#e6f3ff]', textColor: 'text-[#0066cc]', border: 'border-[#e6f3ff]' },
      'COMPLETED': { text: 'Completed', bg: 'bg-[#e6ffe6]', textColor: 'text-[#006600]', border: 'border-[#e6ffe6]' },
      'DRAFT': { text: 'Draft', bg: 'bg-[#fff3c5]', textColor: 'text-[#bf9409]', border: 'border-[#fff3c5]' },
      'Ready for Review': { text: 'Ready for review', bg: 'bg-white', textColor: 'text-gray-800', border: 'border-gray-300' },
      'Not Started': { text: 'Not started', bg: 'bg-[#f3f8fb]', textColor: 'text-[#475d7c]', border: 'border-[#f3f8fb]' },
      'In Progress': { text: 'In progress', bg: 'bg-[#f6e6f3]', textColor: 'text-[#9e007e]', border: 'border-[#f6e6f3]' },
      'In Review': { text: 'In review', bg: 'bg-[#e6f3ff]', textColor: 'text-[#0066cc]', border: 'border-[#e6f3ff]' },
      'Completed': { text: 'Completed', bg: 'bg-[#e6ffe6]', textColor: 'text-[#006600]', border: 'border-[#e6ffe6]' },
      'Draft': { text: 'Draft', bg: 'bg-[#fff3c5]', textColor: 'text-[#bf9409]', border: 'border-[#fff3c5]' },
      'ready-review': { text: 'Ready for review', bg: 'bg-white', textColor: 'text-gray-800', border: 'border-gray-300' },
      'not-started': { text: 'Not started', bg: 'bg-[#f3f8fb]', textColor: 'text-[#475d7c]', border: 'border-[#f3f8fb]' },
      'in-progress': { text: 'In progress', bg: 'bg-[#f6e6f3]', textColor: 'text-[#9e007e]', border: 'border-[#f6e6f3]' },
      'in-review': { text: 'In review', bg: 'bg-[#e6f3ff]', textColor: 'text-[#0066cc]', border: 'border-[#e6f3ff]' },
      'completed': { text: 'Completed', bg: 'bg-[#e6ffe6]', textColor: 'text-[#006600]', border: 'border-[#e6ffe6]' },
      'draft': { text: 'Draft', bg: 'bg-[#fff3c5]', textColor: 'text-[#bf9409]', border: 'border-[#fff3c5]' }
    };
    return statusMap[status] || { text: status, bg: 'bg-gray-100', textColor: 'text-gray-800', border: 'border-gray-100' };
  };

  useEffect(() => {
    dispatch(activeRFIList());
  }, [dispatch]);

  const projects = Array.isArray(activeProjects) ? activeProjects : [];

  const handleProjectClick = async (projectId) => {
    try {
      // Dispatch the getRFIDetails action to call the API
      const result = await dispatch(getRFIDetails(projectId));
      
      if (getRFIDetails.fulfilled.match(result)) {
        // API call successful, store data in localStorage and navigate
        const responseData = result.payload;
        localStorage.setItem(`response_${projectId}`, JSON.stringify(responseData));
        navigate(`/response/${projectId}`);
      } else {
        // API call failed, handle error
        console.error('Failed to fetch response details:', result.payload);
        // You can show an error message to the user here
        alert('Failed to load project details. Please try again.');
      }
    } catch (error) {
      console.error('Error loading response:', error);
      alert('An error occurred while loading the project. Please try again.');
    }
  };

  return (
    <div className="flex-1 bg-white">
      <div className="max-w-7xl mx-auto">
        {/* Upload Section */}
        <FileUploader />

        {/* Active Projects Section */}
        <div className="bg-light-gray border border-gray-200 py-12 px-10">
          <h2 className="text-lg font-semibold text-primary">Active RFI/RFP Projects</h2>

          {loading ? (
            <p className="mt-4 text-sm text-gray-600">Loading projects...</p>
          ) : (
            <div className="py-6">
              {projects.length === 0 ? (
                <p className="text-sm text-gray-600">No active projects found.</p>
              ) : (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {projects.map((project) => (
                    <div
                      key={project.id}
                      onClick={() => handleProjectClick(project.id)}
                      className={`cursor-pointer border-2 border-transparent rounded-lg p-6 hover:shadow-md transition-shadow bg-white hover:border-secondary ${
                        responseDetailsLoading ? 'opacity-50 pointer-events-none' : ''
                      }`}
                    >
                      <div className="flex justify-between items-start mb-4">
                        <span className={`px-2 py-1 text-[10px] font-semibold rounded-md uppercase border ${getStatusConfig(project.status).border} ${getStatusConfig(project.status).bg} ${getStatusConfig(project.status).textColor}`}>
                          {getStatusConfig(project.status).text}
                        </span>
                        <span className="text-xs text-gray-500">
                          Updated: {timeAgo(project.updated)}
                        </span>
                      </div>

                      <h3 className="text-sm font-semibold text-gray-900">{project.title}</h3>
                      <p className="text-xs mb-3">Due Date: {new Date(project.dueDate).toLocaleDateString()}</p>
                      <p className="text-xs text-gray-600 mb-3">Section: {project.section}</p>

                      <div className="mb-4">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-gray-700">Progress: {project.progress}%</span>
                          <div className="flex-1 bg-gray-300 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${project.progress}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-600">Users Assigned:</span>
                        <div className="flex -space-x-2">
                          {project.users && project.users.length > 0 ? (
                            <>
                              {project.users.slice(0, 3).map((user, index) => (
                                <div
                                  key={index}
                                  className={`w-6 h-6 rounded-full ${index === 0 ? 'bg-blue-500' : index === 1 ? 'bg-green-500' : 'bg-purple-500'} flex items-center justify-center text-xs font-semibold text-white border-2 border-white`}
                                  title={user.name}
                                >
                                  {user.name.charAt(0)}
                                </div>
                              ))}
                              {project.users.length > 3 && (
                                <div className="w-6 h-6 rounded-full bg-[#9e007e] flex items-center justify-center text-xs font-semibold text-white border-2 border-white">
                                  +{project.users.length - 3}
                                </div>
                              )}
                            </>
                          ) : (
                            <span className="text-xs text-gray-500">No Assigned Users</span>
                          )}
                        </div>
                      </div>

                      {/* Loading indicator when fetching response details */}
                      {responseDetailsLoading && (
                        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 rounded-lg">
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-secondary"></div>
                            Loading...
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}