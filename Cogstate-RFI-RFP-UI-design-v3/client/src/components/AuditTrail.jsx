import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { getAuditTrail } from "../state/reducers/AuditTrail";
import { Sparkles, Edit, CheckCircle, FileText } from "lucide-react";
import auditTrailMock from "../mock/auditTrailMock";

export default function AuditTrail({ responseId }) {
  const dispatch = useDispatch();
  const { auditTrail, loading, error } = useSelector(state => state.auditTrail ?? {});

  useEffect(() => {
    if (responseId) {
      dispatch(getAuditTrail({ id: responseId }));
    }
  }, [dispatch, responseId]);

  // Debug logging
  console.log("AuditTrail Debug:", { responseId, auditTrail, loading, error });

  const logData = auditTrail || [];

  const sortedLog = [...logData].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

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

  return (
    <div className="min-h-screen bg-light-gray">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Project Audit Trail</h3>

          {loading && <p className="text-gray-500">Loading audit trail...</p>}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
              <p className="text-red-800 font-medium">Error loading audit trail:</p>
              <p className="text-red-600 text-sm mt-1">{error}</p>
            </div>
          )}

          <div className="flow-root">
            <ul role="list" className="-mb-8">
              {sortedLog.map((event, eventIdx) => (
                <li key={event.id}>
                  <div className="relative pb-8">
                    {eventIdx !== sortedLog.length - 1 && (
                      <span className="absolute left-4 top-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true" />
                    )}
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
                          {event.question && (
                            <p className="mt-1 text-xs text-gray-500 italic border-l-2 border-gray-200 pl-2">
                              Regarding: "{event.question}"
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
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
