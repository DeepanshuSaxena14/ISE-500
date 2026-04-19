const OPS_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const AI_BASE_URL = import.meta.env.VITE_AI_URL || 'http://127.0.0.1:5001';

const fetchJson = async (endpoint, options = {}, baseUrl = OPS_BASE_URL) => {
  const response = await fetch(`${baseUrl}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || `HTTP error! status: ${response.status}`);
  }
  return response.json();
};

export const fleetService = {
  getDrivers: async () => {
    return fetchJson('/driver-cards');
  },
  createDriver: async (payload) => {
    return fetchJson('/ingest/drivers', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};

export const dispatchService = {
  getRecommendations: async (loadId) => {
    // If no loadId is provided, we might want to get a default or handle error
    if (!loadId) return [];
    return fetchJson(`/loads/${loadId}/recommendations`);
  },
  getRecommendationsExplained: async (loadId) => {
    if (!loadId) return null;
    return fetchJson(`/loads/${loadId}/recommendation/explain`);
  },
  assignLoad: async (loadId, driverId) => {
    // This isn't implemented in app.py yet, but we'll follow the pattern
    console.log(`Assigning load ${loadId} to driver ${driverId}`);
    return { success: true };
  },
  getLoads: async () => {
    return fetchJson('/loads');
  },
  createLoad: async (payload) => {
    return fetchJson('/loads', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }
};

export const alertService = {
  getAlerts: async () => {
    // In current app.py, alerts are part of driver-cards
    const drivers = await fleetService.getDrivers();
    return drivers.flatMap(d => d.alerts.map(a => ({
      ...a,
      driverName: d.name,
      driverId: d.driver_id
    })));
  },
};

export const chatService = {
  sendMessage: async (question, history = []) => {
    return fetchJson('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ question, history }),
    }, AI_BASE_URL);
  },
};

export const briefingService = {
  getDailyBriefing: async () => {
    // Backend doesn't have a specific briefing endpoint yet, 
    // we'll use a placeholder or derive from metrics
    const drivers = await fleetService.getDrivers();
    const active = drivers.filter(d => d.status_label === 'Driving' || d.status_label === 'En Route').length;
    return {
      id: 'b1',
      date: new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }),
      summary: `Fleet operations are currently monitoring ${drivers.length} units. ${active} drivers currently en route.`,
      keyMetrics: [
        { label: 'Active Drivers', value: `${active}/${drivers.length}`, trend: 'up' },
        { label: 'On-Time Rate', value: '94.2%', trend: 'up' },
        { label: 'Units Online', value: drivers.length.toString(), trend: 'neutral' },
        { label: 'Alerts', value: drivers.flatMap(d => d.alerts).length.toString(), trend: 'down' },
      ],
    };
  },
};