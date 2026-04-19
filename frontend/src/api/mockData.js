export const mockDrivers = [
  { id: '1', name: 'Alex Rivera', status: 'active', location: 'Chicago, IL', load: 'Medical Supplies', eta: '2h 15m', efficiency: 94 },
  { id: '2', name: 'Sarah Chen', status: 'active', location: 'Denver, CO', load: 'Electronics', eta: '45m', efficiency: 98 },
  { id: '3', name: 'Marcus Miller', status: 'warning', location: 'Atlanta, GA', load: 'Perishables', eta: 'Delayed (Traffic)', efficiency: 82 },
  { id: '4', name: 'Leila Smith', status: 'idle', location: 'Phoenix, AZ', load: 'None', eta: '-', efficiency: 88 },
  { id: '5', name: 'Jakob Wagner', status: 'active', location: 'Seattle, WA', load: 'Industrial Parts', eta: '3h 10m', efficiency: 91 },
  { id: '6', name: 'Elena Petrova', status: 'offline', location: 'Miami, FL', load: 'Furniture', eta: '-', efficiency: 75 },
  { id: '7', name: 'Omar Hassan', status: 'active', location: 'Austin, TX', load: 'Automotive', eta: '1h 05m', efficiency: 96 },
  { id: '8', name: 'Chloe Dubois', status: 'warning', location: 'Boston, MA', load: 'Textiles', eta: 'Weather Alert', efficiency: 85 },
];

export const mockRecommendations = [
  {
    id: 'rec1',
    driverId: '4',
    driverName: 'Leila Smith',
    route: 'Phoenix -> San Diego',
    score: 92,
    reason: 'Highest proximity to pickup location with optimal fuel efficiency.',
    estimatedSavings: '$140',
  },
  {
    id: 'rec2',
    driverId: '6',
    driverName: 'Elena Petrova',
    route: 'Miami -> Orlando',
    score: 88,
    reason: 'Rest cycle completed. Urgent medical load available.',
    estimatedSavings: '$85',
  },
];

export const mockAlerts = [
  {
    id: 'a1',
    severity: 'critical',
    title: 'Engine Fault - Unit 402',
    description: 'Vehicle #402 (Marcus Miller) reporting engine temperature anomaly.',
    timestamp: '2024-05-20T10:30:00Z',
  },
  {
    id: 'a2',
    severity: 'high',
    title: 'Weather Delay - Route I-80',
    description: 'Heavy snow affecting visibility on I-80 West. Expect 2h delays.',
    timestamp: '2024-05-20T11:15:00Z',
  },
  {
    id: 'a3',
    severity: 'medium',
    title: 'Load Re-assignment',
    description: 'Load #A23 assigned to Sarah Chen following optimization.',
    timestamp: '2024-05-20T09:45:00Z',
  },
];

export const mockBriefing = {
  id: 'b1',
  date: 'May 20, 2024',
  summary: 'Overall fleet efficiency is up 4% today. 3 major weather alerts in the Northeast corridor. Fuel costs stabilized after midday price adjustments.',
  keyMetrics: [
    { label: 'Active Drivers', value: '72/80', trend: 'up' },
    { label: 'On-Time Rate', value: '94.2%', trend: 'up' },
    { label: 'Fuel Efficiency', value: '8.4 MPG', trend: 'neutral' },
    { label: 'Safety Incidents', value: '0', trend: 'down' },
  ],
};
