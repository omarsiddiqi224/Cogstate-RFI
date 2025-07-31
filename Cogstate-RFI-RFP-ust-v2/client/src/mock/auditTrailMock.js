const auditTrailMock = [
  { id: 'at1', timestamp: '2025-07-10T23:20:00Z', actor: 'AI (Gemini)', action: 'Generated initial draft for question 2.1.', question: 'What are the primary safety protocols for data handling?', type: 'AI' },
  { id: 'at2', timestamp: '2025-07-10T23:35:12Z', actor: 'DM_Lead', action: 'Edited response for question 2.1.', question: 'What are the primary safety protocols for data handling?', type: 'EDIT' },
  { id: 'at3', timestamp: '2025-07-11T00:02:45Z', actor: 'CR_Head', action: 'Marked question 2.3 as complete.', question: 'What measures are in place for risk assessment?', type: 'COMPLETE' },
  { id: 'at4', timestamp: '2025-07-11T01:10:05Z', actor: 'Safety_Officer', action: 'Edited response for question 2.4.', question: 'What measures are in place for risk assessment?', type: 'EDIT' },
  { id: 'at5', timestamp: '2025-07-11T01:15:21Z', actor: 'Safety_Officer', action: 'Describe the incident response procedures.', question: 'Describe the incident response procedures.', type: 'COMPLETE' },
  { id: 'at6', timestamp: '2025-07-21T01:30:00Z', actor: 'AI (Gemini)', action: 'Generated initial draft for question 2.2.', question: 'How do you ensure compliance with regulatory requirements?', type: 'AI' }
];

export default auditTrailMock;