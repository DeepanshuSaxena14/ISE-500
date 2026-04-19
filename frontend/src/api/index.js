import { mockDrivers, mockRecommendations, mockAlerts, mockBriefing } from './mockData';

// ops backend (port 8000) — handles drivers, loads, dispatch scoring
const OPS_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
// AI backend (port 5001) — handles chat via Groq + LangChain
const AI_URL = import.meta.env.VITE_AI_URL || 'http://localhost:5001';

async function apiFetch(url, options = {}) {
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`[api] fetch failed for ${url}:`, err.message);
    return null;
  }
}
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const fetchJson = async (endpoint, options = {}) => {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
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
    const data = await apiFetch(`${OPS_URL}/driver-cards`);
    if (data && Array.isArray(data.drivers)) return data.drivers;
    // Fallback to mock if backend unreachable
    console.warn('[fleetService] falling back to mock drivers');
    return mockDrivers;
    return fetchJson('/driver-cards');
  },
  createDriver: async (payload) => {
    return fetchJson('/ingest/drivers', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  createDriver: async (payload) => {
    return fetchJson('/ingest/drivers', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};

export const dispatchService = {
  getRecommendations: async (loadId = 'LD-4821') => {
    const data = await apiFetch(`${OPS_URL}/loads/${loadId}/recommendations`);
    if (data && Array.isArray(data.recommendations)) return data.recommendations;
    console.warn('[dispatchService] falling back to mock recommendations');
    return mockRecommendations;
    getRecommendations: async (loadId) => {
      // If no loadId is provided, we might want to get a default or handle error
      if (!loadId) return [];
      return fetchJson(`/loads/${loadId}/recommendations`);
    },
      getRecommendationsExplained: async (loadId) => {
        if (!loadId) return null;
        return fetchJson(`/loads/${loadId}/recommendation/explain`);
      },
        getRecommendationsExplained: async (loadId) => {
          if (!loadId) return null;
          return fetchJson(`/loads/${loadId}/recommendation/explain`);
        },
          assignLoad: async (loadId, driverId) => {
            // POST to ops backend once that endpoint exists; graceful stub for now
            console.log(`[dispatchService] assigning load ${loadId} to driver ${driverId}`);
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
        // Alerts are derived from driver data — fetch driver-cards and extract alerts
        const data = await apiFetch(`${OPS_URL}/driver-cards`);
        if (data && Array.isArray(data.drivers)) {
          const alerts = [];
          data.drivers.forEach(driver => {
            (driver.alerts || []).forEach(alert => {
              alerts.push({
                id: `${driver.id}-${Math.random().toString(36).substr(2, 5)}`,
                driverId: driver.id,
                driverName: driver.name,
                severity: alert.severity || 'medium',
                message: alert.text || alert,
                timestamp: new Date().toISOString(),
              });
            });
          });
          if (alerts.length > 0) return alerts;
        }
        console.warn('[alertService] falling back to mock alerts');
        return mockAlerts;
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
      // sendMessage routes to the Flask AI layer on port 5001
      sendMessage: async (message, history = []) => {
        const data = await apiFetch(`${AI_URL}/api/chat`, {
          method: 'POST',
          body: JSON.stringify({ question: message, history }),
        });
        if (data && !data.error) {
          return {
            id: Math.random().toString(36).substr(2, 9),
            role: 'assistant',
            content: data,          // full structured AI response
            timestamp: new Date().toISOString(),
          };
        }
        // Fallback
        console.warn('[chatService] falling back to stub response');
        return {
          id: Math.random().toString(36).substr(2, 9),
          role: 'assistant',
          content: `I've analyzed the current fleet metrics. Regarding "${message}" — please ensure the AI backend (port 5001) is running.`,
          timestamp: new Date().toISOString(),
        };
        sendMessage: async (question, history = []) => {
          return fetchJson('/api/chat', {
            method: 'POST',
            body: JSON.stringify({ question, history }),
          });
        },
};

      export const briefingService = {
        getDailyBriefing: async () => {
          // Briefing is generated by the AI layer — future endpoint: GET /api/briefing
          const data = await apiFetch(`${AI_URL}/api/briefing`);
          if (data && !data.error) return data;
          console.warn('[briefingService] falling back to mock briefing');
          return mockBriefing;
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