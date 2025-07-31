import React from 'react';

export default function Dashboard() {

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="bg-white text-white px-6 py-4">
        <h1 className="text-xl font-bold text-primary">Dashboard</h1>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Content */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        Content for Dashboard will be displayed here. This is a placeholder.  
        </div>
      </div>
    </div>
  );
}