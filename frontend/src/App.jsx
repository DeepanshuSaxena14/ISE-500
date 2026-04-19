import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { DashboardLayout } from './layouts/DashboardLayout';
import FleetDashboard from './pages/FleetDashboard';
import SmartDispatch from './pages/SmartDispatch';
import AIChatAssistant from './pages/AIChatAssistant';
import Alerts from './pages/Alerts';
import Briefings from './pages/Briefings';
import Settings from './pages/Settings';

function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardLayout />}>
        <Route index element={<FleetDashboard />} />

        <Route path="dispatch" element={<SmartDispatch />} />
        <Route path="chat" element={<AIChatAssistant />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="briefings" element={<Briefings />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

export default App;
