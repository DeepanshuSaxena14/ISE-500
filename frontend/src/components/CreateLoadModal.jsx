import React, { useState, useEffect, useRef } from 'react';
import { X, MapPin, Loader2 } from 'lucide-react';

export function CreateLoadModal({ isOpen, onClose, onSave }) {
  const [formData, setFormData] = useState({
    name: 'New Trip',
    origin: 'Los Angeles, CA',
    originLat: 34.0522,
    originLng: -118.2437,
    destination: 'San Francisco, CA',
    destinationLat: 37.7749,
    destinationLng: -122.4194,
    pickupTime: new Date().toISOString().slice(0, 16),
    dropoffTime: new Date(Date.now() + 86400000).toISOString().slice(0, 16),
    heightFt: '13',
    heightIn: '6',
    widthFt: '8',
    widthIn: '6',
    lengthFt: '53',
    lengthIn: '0',
    weight: '80000',
    singleAxle: '20000',
    axles: '5',
    trailers: '1',
    isHazmat: false
  });

  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState({ origin: [], destination: [] });
  const [searching, setSearching] = useState({ origin: false, destination: false });
  const debounceTimer = useRef(null);

  if (!isOpen) return null;

  const fetchSuggestions = async (query, field) => {
    if (query.length < 3) {
      setSuggestions(prev => ({ ...prev, [field]: [] }));
      return;
    }

    setSearching(prev => ({ ...prev, [field]: true }));
    try {
      // Photon API: filter for USA if possible, but query usually handles it
      const resp = await fetch(`https://photon.komoot.io/api/?q=${encodeURIComponent(query)}&limit=5`);
      const data = await resp.json();
      
      const mapped = data.features.map(f => ({
        label: [
          f.properties.name,
          f.properties.city,
          f.properties.state,
          f.properties.postcode
        ].filter(Boolean).join(", "),
        lat: f.geometry.coordinates[1],
        lng: f.geometry.coordinates[0]
      }));

      setSuggestions(prev => ({ ...prev, [field]: mapped }));
    } catch (err) {
      console.error("Geocoding error:", err);
    } finally {
      setSearching(prev => ({ ...prev, [field]: false }));
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      fetchSuggestions(value, field);
    }, 400);
  };

  const handleSelectSuggestion = (field, sug) => {
    setFormData(prev => ({
      ...prev,
      [field]: sug.label,
      [`${field}Lat`]: sug.lat,
      [`${field}Lng`]: sug.lng
    }));
    setSuggestions(prev => ({ ...prev, [field]: [] }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    const payload = {
      pickup_name: formData.origin.split(',')[0],
      pickup_address: formData.origin,
      pickup_lat: formData.originLat,
      pickup_lng: formData.originLng,
      dropoff_name: formData.destination.split(',')[0],
      dropoff_address: formData.destination,
      dropoff_lat: formData.destinationLat,
      dropoff_lng: formData.destinationLng,
      pickup_time: formData.pickupTime,
      dropoff_time: formData.dropoffTime,
      required_trailer_type: formData.trailers > 1 ? 'DOUBLE' : 'DRY_VAN',
      required_vehicle_type: 'TRUCK',
      metadata: {
        height: `${formData.heightFt}'${formData.heightIn}"`,
        weight: formData.weight,
        axles: formData.axles,
        hazmat: formData.isHazmat
      }
    };

    try {
      await onSave(payload);
      onClose();
    } catch (err) {
      console.error("Failed to create load", err);
      alert("Error creating load: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const SuggestionBox = ({ field }) => (
    suggestions[field].length > 0 && (
      <div className="absolute z-50 left-0 right-0 mt-1 bg-[#1a1c24] border border-white/10 rounded-xl shadow-2xl overflow-hidden max-h-60 overflow-y-auto">
        {suggestions[field].map((sug, i) => (
          <button
            key={i}
            type="button"
            onClick={() => handleSelectSuggestion(field, sug)}
            className="w-full px-4 py-3 text-left text-xs text-white/70 hover:bg-brand-primary hover:text-white transition-colors border-b border-white/5 last:border-0 flex items-start gap-3"
          >
            <MapPin className="w-3.5 h-3.5 mt-0.5 shrink-0" />
            <span>{sug.label}</span>
          </button>
        ))}
      </div>
    )
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-brand-bg border border-white/10 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl animate-in zoom-in duration-200">
        <div className="flex items-center justify-between p-6 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-brand-primary/10 rounded-lg">
              <MapPin className="w-5 h-5 text-brand-primary" />
            </div>
            <h2 className="text-xl font-bold tracking-tight">Add Trip Details</h2>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full transition-colors text-white/40 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-8 space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div className="col-span-2">
              <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-2 block">Trip Name / Reference</label>
              <input 
                required
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-brand-primary transition-colors"
                value={formData.name}
                onChange={e => setFormData({...formData, name: e.target.value})}
                placeholder="e.g. Load 45-A-901"
              />
            </div>

            <div className="col-span-1 relative">
              <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-2 block">Origin</label>
              <div className="relative">
                <input 
                  required
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-brand-primary transition-colors"
                  value={formData.origin}
                  onChange={e => handleInputChange('origin', e.target.value)}
                  placeholder="Street address, city, or zip"
                />
                {searching.origin && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-primary animate-spin" />}
              </div>
              <SuggestionBox field="origin" />
            </div>

            <div className="col-span-1 relative">
              <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-2 block">Destination</label>
              <div className="relative">
                <input 
                  required
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-brand-primary transition-colors"
                  value={formData.destination}
                  onChange={e => handleInputChange('destination', e.target.value)}
                  placeholder="Street address, city, or zip"
                />
                {searching.destination && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-primary animate-spin" />}
              </div>
              <SuggestionBox field="destination" />
            </div>

            <div className="col-span-1">
              <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-2 block">Weight (lbs)</label>
              <input className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm" value={formData.weight} onChange={e => setFormData({...formData, weight: e.target.value})} />
            </div>

            <div className="col-span-1 flex gap-4">
              <div className="flex-1">
                <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-2 block">Axles</label>
                <select className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm appearance-none" value={formData.axles} onChange={e => setFormData({...formData, axles: e.target.value})}>
                  {[1,2,3,4,5,6,7,8].map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
              <div className="flex-1">
                <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-2 block">Trailers</label>
                <select className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm appearance-none" value={formData.trailers} onChange={e => setFormData({...formData, trailers: e.target.value})}>
                  {[1,2,3].map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
            </div>
          </div>

          <label className="flex items-center gap-3 cursor-pointer group pt-2">
            <input 
              type="checkbox" 
              className="w-5 h-5 rounded border-white/10 bg-white/5 text-brand-primary focus:ring-brand-primary focus:ring-offset-0"
              checked={formData.isHazmat}
              onChange={e => setFormData({...formData, isHazmat: e.target.checked})}
            />
            <span className="text-[12px] text-white/60 group-hover:text-white transition-colors">Transporting hazardous material (Hazmat)</span>
          </label>

          <div className="flex items-center justify-end gap-4 pt-4 border-t border-white/5">
            <button 
              type="button" 
              onClick={onClose} 
              className="px-6 py-2.5 text-xs font-bold text-white/40 hover:text-white transition-colors tracking-widest"
            >
              CANCEL
            </button>
            <button 
              type="submit"
              disabled={loading}
              className="bg-brand-primary text-white px-10 py-2.5 rounded-xl font-bold text-xs tracking-widest hover:brightness-110 active:scale-95 transition-all shadow-lg shadow-brand-primary/20 disabled:opacity-50"
            >
              {loading ? 'CREATING TRIP...' : 'CREATE TRIP'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
