import { mockDrivers, mockRecommendations, mockAlerts, mockBriefing } from './mockData';

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export const fleetService = {
  getDrivers: async () => {
    await sleep(500);
    // Placeholder for: fetch(`${import.meta.env.VITE_API_URL}/fleet`)
    return mockDrivers;
  },
};

export const dispatchService = {
  getRecommendations: async () => {
    await sleep(800);
    // Placeholder for: fetch(`${import.meta.env.VITE_API_URL}/dispatch/recommend`)
    return mockRecommendations;
  },
  assignLoad: async (recommendationId) => {
    await sleep(400);
    console.log(`Assigning load for recommendation: ${recommendationId}`);
    return { success: true };
  },
};

export const alertService = {
  getAlerts: async () => {
    await sleep(600);
    // Placeholder for: fetch(`${import.meta.env.VITE_API_URL}/alerts`)
    return mockAlerts;
  },
};

export const chatService = {
  sendMessage: async (message) => {
    await sleep(1000);
    // Placeholder for: fetch(`${import.meta.env.VITE_API_URL}/chat`, { method: 'POST', body: JSON.stringify({ message }) })
    return {
      id: Math.random().toString(36).substr(2, 9),
      role: 'assistant',
      content: `I've analyzed the current fleet metrics. Regarding "${message}", Driver 4 (Leila Smith) in Phoenix is currently idle and the most efficient choice for a San Diego dispatch.`,
      timestamp: new Date().toISOString(),
    };
  },
};

export const briefingService = {
  getDailyBriefing: async () => {
    await sleep(700);
    // Placeholder for: fetch(`${import.meta.env.VITE_API_URL}/briefing/generate`)
    return mockBriefing;
  },
};
