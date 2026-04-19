import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, 
  ChevronRight, 
  Navigation, 
  Clock, 
  MapPin, 
  Filter, 
  Plus, 
  Maximize2, 
  Layers,
  MessageCircle,
  Settings
} from 'lucide-react';
import { CreateLoadModal } from '../components/CreateLoadModal';
import { dispatchService } from '../api';

export default function AddLoadWithLocation() {
  const navigate = useNavigate();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [trips, setTrips] = useState([]);
  const [selectedTripId, setSelectedTripId] = useState(null);

  useEffect(() => {
    fetchTrips();
  }, []);

  const fetchTrips = async () => {
    try {
      const data = await dispatchService.getLoads();
      setTrips(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Only initialize if the map container exists and Leaflet is loaded
    if (!document.getElementById('map-container') || !window.L) return;

    // Center on USA by default or use first trip
    const defaultCenter = [39.8283, -98.5795];
    const defaultZoom = 4;

    const map = window.L.map('map-container', {
      zoomControl: false,
      attributionControl: false
    }).setView(defaultCenter, defaultZoom);

    // Dark Matter Tile Layer (CartoDB)
    window.L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      subdomains: 'abcd',
      maxZoom: 20
    }).addTo(map);

    // Add zoom control to a better position
    window.L.control.zoom({ position: 'bottomright' }).addTo(map);

    const markers = [];
    const tripBounds = {};

    // Add markers for all trips
    trips.forEach(trip => {
      const pLat = trip.pickup_lat || 34.0522;
      const pLng = trip.pickup_lng || -118.2437;
      const dLat = trip.dropoff_lat || 37.7749;
      const dLng = trip.dropoff_lng || -122.4194;

      const currentTripMarkers = [[pLat, pLng], [dLat, dLng]];
      tripBounds[trip.id] = currentTripMarkers;

      // Pickup Marker
      window.L.circleMarker([pLat, pLng], {
        radius: 6,
        fillColor: "#1d9e75",
        color: "#fff",
        weight: 2,
        opacity: 1,
        fillOpacity: 1
      }).addTo(map).bindPopup(`<b>Pickup:</b> ${trip.pickup_name || 'Origin'}`);

      // Dropoff Marker
      window.L.circleMarker([dLat, dLng], {
        radius: 6,
        fillColor: "#60a5fa",
        color: "#fff",
        weight: 2,
        opacity: 1,
        fillOpacity: 1
      }).addTo(map).bindPopup(`<b>Dropoff:</b> ${trip.dropoff_name || 'Destination'}`);

      // Route Line
      window.L.polyline([[pLat, pLng], [dLat, dLng]], {
        color: trip.id === selectedTripId ? '#1d9e75' : '#1d9e75',
        weight: trip.id === selectedTripId ? 4 : 2,
        opacity: trip.id === selectedTripId ? 0.8 : 0.4,
        dashArray: '5, 10'
      }).addTo(map);

      markers.push(...currentTripMarkers);
    });

    // Handle focusing
    if (selectedTripId && tripBounds[selectedTripId]) {
      map.fitBounds(window.L.latLngBounds(tripBounds[selectedTripId]), { padding: [100, 100], maxZoom: 12 });
    } else if (markers.length > 0) {
      map.fitBounds(window.L.latLngBounds(markers), { padding: [50, 50] });
    }

    return () => {
      map.remove();
    };
  }, [trips, selectedTripId]);

  const handleCreateLoad = async (payload) => {
    const newLoad = await dispatchService.createLoad(payload);
    // After creating a load, we navigate to the dispatch page to rank drivers
    navigate('/dispatch', { state: { selectedLoadId: newLoad.id } });
  };

  return (
    <div className="flex flex-col h-full -m-6 relative overflow-hidden">
      {/* ── TOP NAV / ROUTING PROFILE ── */}

      <div className="flex-1 flex min-h-0">
        {/* ── SIDEBAR ── */}
        <div className="w-96 bg-brand-bg border-r border-white/5 flex flex-col z-20">
          <div className="p-6 border-b border-white/5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-white mb-1">Add Load</h2>
              <p className="text-xs text-white/40">Manage trips & dispatch</p>
            </div>
            <button 
              onClick={() => setIsModalOpen(true)}
              className="bg-brand-primary text-white p-2 rounded-lg hover:brightness-110 active:scale-95 transition-all shadow-lg shadow-brand-primary/20"
              title="Create New Trip"
            >
              <Plus className="w-5 h-5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-brand-primary uppercase tracking-widest border-b border-brand-primary pb-1">Recent Trips</span>
            </div>

            <div className="space-y-3">
              {trips.length === 0 ? (
                <div className="p-8 text-center border border-dashed border-white/10 rounded-2xl">
                  <p className="text-xs text-white/30">No active trips found.</p>
                  <button 
                    onClick={() => setIsModalOpen(true)}
                    className="mt-3 text-[11px] font-bold text-brand-primary hover:underline uppercase tracking-widest"
                  >
                    + Create First Trip
                  </button>
                </div>
              ) : (
                trips.map((trip, i) => (
                  <div 
                    key={trip.id} 
                    onClick={() => setSelectedTripId(trip.id)}
                    className={`bg-white/[0.03] border rounded-xl p-4 hover:bg-white/[0.06] transition-all cursor-pointer group ${
                      selectedTripId === trip.id ? 'border-brand-primary/50 bg-white/[0.06]' : 'border-white/5'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="text-[13px] font-bold text-white/90 group-hover:text-white">TRIP-{trip.id.slice(0, 6).toUpperCase()}</div>
                      <span className="text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 bg-amber-500/10 border border-amber-500/20 text-amber-500 rounded">Scheduled</span>
                    </div>
                    <div className="space-y-2 relative pl-4 border-l border-white/10 ml-1">
                      <div className="text-[11px] font-bold text-white/80">{trip.pickup_name || trip.origin}</div>
                      <div className="text-[11px] font-bold text-white/80">{trip.dropoff_name || trip.destination}</div>
                      <div className="absolute top-0 -left-[5px] w-2 h-2 rounded-full border border-white/40 bg-brand-bg" />
                      <div className="absolute bottom-0 -left-[5px] w-2 h-2 rounded-full border border-teal-500 bg-teal-500 shadow-[0_0_8px_rgba(20,184,166,0.6)]" />
                    </div>
                    <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-[10px] text-white/40 font-bold">
                       <span className="flex items-center gap-1.5"><Clock className="w-3 h-3" /> {new Date(trip.pickup_time || Date.now()).toLocaleDateString()}</span>
                       <button 
                         onClick={(e) => {
                           e.stopPropagation();
                           navigate('/dispatch', { state: { selectedLoadId: trip.id } });
                         }}
                         className="flex items-center gap-1.5 hover:text-brand-primary transition-colors text-white/40"
                       >
                         <Navigation className="w-3 h-3" /> Ready for Dispatch
                       </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* ── MAP AREA ── */}
        <div className="flex-1 bg-[#0b0c10] relative z-10" id="map-container" style={{ minHeight: '400px' }}>
          {/* Leaflet map will be mounted here */}
        </div>
      </div>

      <CreateLoadModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onSave={handleCreateLoad} 
      />

      <style>{`
        @keyframes dash {
          to { stroke-dashoffset: -1000; }
        }
      `}</style>
    </div>
  );
}
