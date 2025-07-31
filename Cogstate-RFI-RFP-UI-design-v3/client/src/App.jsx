import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux'; 
import { store } from './state/store';
import Layout from './layout/Layout';
import RfiRfp from './pages/Rfi-Rfp';
import ResponsePage from './pages/ResponsePage';
import Dashboard from './pages/Dashboard';
import KnowledgeBase from './pages/KnowledgeBase';

export default function App() {
  return (
    <Provider store={store}>
      <Router>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="rfi-rfp" element={<RfiRfp />} />
            <Route path="knowledgebase" element={<KnowledgeBase />} />
            <Route path="response/:id" element={<ResponsePage />} />
          </Route>
        </Routes>
      </Router>
    </Provider>
  );
}
