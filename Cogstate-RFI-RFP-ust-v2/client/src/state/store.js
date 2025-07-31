import { configureStore } from '@reduxjs/toolkit';
import fileReducer from './reducers/fileReducer';
import knowledgeBaseReducer from './reducers/knowledgeBase';
import auditTrailReducer from './reducers/AuditTrail';
import responseReducer from './reducers/ResponsePage';
import rfiReducer from './reducers/rfi';

export const store = configureStore({
  reducer: {
    file: fileReducer,
    kb: knowledgeBaseReducer,
    auditTrail: auditTrailReducer,
    response: responseReducer,
    rfi: rfiReducer,
  },
});
