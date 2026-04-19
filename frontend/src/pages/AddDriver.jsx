import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  UserPlus, 
  ArrowLeft, 
  Check, 
  ShieldCheck, 
  Briefcase, 
  Phone, 
  Mail, 
  MapPin,
  Truck
} from 'lucide-react';
import { fleetService } from '../api';

const DRIVER_TYPES = ["COMPANY", "OWNER_OPERATOR", "CONTRACTOR"];
const WORK_STATUSES = ["AVAILABLE", "OFF_DUTY", "IN_TRANSIT"];

export default function AddDriver() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    carrier: 'DISPATCHIQ FLEET',
    work_status: 'AVAILABLE',
    terminal: 'Main Terminal (Tempe)',
    driver_type: 'COMPANY',
    phone: '',
    email: '',
    last_known_location: 'Main Terminal',
    timezone: 'UTC'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      // Map the flat UI form to the nested ingest/drivers structure
      const ingestPayload = {
        data: [{
          driver_id: Math.floor(Math.random() * 900000) + 100000, // Generate temporary unique ID
          basic_info: {
            driver_first_name: formData.first_name,
            driver_last_name: formData.last_name,
            carrier: formData.carrier,
            work_status: formData.work_status,
            terminal: formData.terminal,
            driver_type: formData.driver_type,
            driver_phone_number: formData.phone,
            driver_email: formData.email
          },
          driver_location: {
            last_known_location: formData.last_known_location || formData.terminal,
            latest_update: Date.now(),
            timezone: formData.timezone
          }
        }]
      };

      await fleetService.createDriver(ingestPayload);
      setSuccess(true);
      setTimeout(() => {
        navigate('/');
      }, 2000);
    } catch (err) {
      console.error(err);
      alert("Failed to onboard driver: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="h-full flex flex-col items-center justify-center animate-in fade-in duration-500">
        <div className="w-20 h-20 bg-brand-primary/20 rounded-full flex items-center justify-center mb-6">
          <Check className="w-10 h-10 text-brand-primary animate-in zoom-in duration-300" />
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">Driver Onboarded</h1>
        <p className="text-brand-muted">Directing you back to the dashboard...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <button 
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-brand-muted hover:text-white transition-colors mb-8 group"
      >
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
        <span className="text-sm font-semibold uppercase tracking-widest">Back to Dashboard</span>
      </button>

      <div className="flex items-center gap-4 mb-10">
        <div className="p-3 bg-brand-primary/10 rounded-2xl border border-brand-primary/20 shadow-lg shadow-brand-primary/5">
          <UserPlus className="w-8 h-8 text-brand-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-1">Onboard New Driver</h1>
          <p className="text-brand-muted">Enter fleet operator details to register them in the system.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="grid grid-cols-2 gap-8">
          {/* PERSONAL INFO */}
          <div className="bg-white/[0.03] border border-white/5 rounded-3xl p-8 space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <ShieldCheck className="w-4 h-4 text-brand-primary" />
              <h3 className="text-xs font-bold text-white uppercase tracking-widest">Personal Identification</h3>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-white/30 uppercase tracking-widest ml-1">First Name</label>
                  <input 
                    required
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-brand-primary transition-all hover:bg-white/[0.07]"
                    value={formData.first_name}
                    onChange={e => setFormData({...formData, first_name: e.target.value})}
                    placeholder="e.g. Marcus"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-white/30 uppercase tracking-widest ml-1">Last Name</label>
                  <input 
                    required
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-brand-primary transition-all hover:bg-white/[0.07]"
                    value={formData.last_name}
                    onChange={e => setFormData({...formData, last_name: e.target.value})}
                    placeholder="e.g. Rivera"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-bold text-white/30 uppercase tracking-widest ml-1">Work Email</label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
                  <input 
                    type="email"
                    className="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-4 py-3 text-sm focus:outline-none focus:border-brand-primary transition-all hover:bg-white/[0.07]"
                    value={formData.email}
                    onChange={e => setFormData({...formData, email: e.target.value})}
                    placeholder="m.rivera@dispatchiq.com"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-bold text-white/30 uppercase tracking-widest ml-1">Phone Number</label>
                <div className="relative">
                  <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
                  <input 
                    className="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-4 py-3 text-sm focus:outline-none focus:border-brand-primary transition-all hover:bg-white/[0.07]"
                    value={formData.phone}
                    onChange={e => setFormData({...formData, phone: e.target.value})}
                    placeholder="+1 (555) 000-0000"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* FLEET ASSIGNMENT */}
          <div className="bg-white/[0.03] border border-white/5 rounded-3xl p-8 space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <Briefcase className="w-4 h-4 text-brand-primary" />
              <h3 className="text-xs font-bold text-white uppercase tracking-widest">Fleet & Operations</h3>
            </div>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-white/30 uppercase tracking-widest ml-1">Driver Type</label>
                <div className="flex gap-2">
                  {DRIVER_TYPES.map(type => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setFormData({...formData, driver_type: type})}
                      className={`flex-1 py-2 rounded-lg text-[10px] font-bold border transition-all ${
                        formData.driver_type === type 
                          ? 'bg-brand-primary/10 border-brand-primary text-brand-primary' 
                          : 'bg-white/5 border-white/10 text-white/40 hover:text-white'
                      }`}
                    >
                      {type.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-bold text-white/30 uppercase tracking-widest ml-1">Assigned Carrier</label>
                <input 
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-brand-primary transition-all"
                  value={formData.carrier}
                  onChange={e => setFormData({...formData, carrier: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-bold text-white/30 uppercase tracking-widest ml-1">Terminal</label>
                <div className="relative">
                  <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
                  <input 
                    className="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-4 py-3 text-sm focus:outline-none focus:border-brand-primary transition-all"
                    value={formData.terminal}
                    onChange={e => setFormData({...formData, terminal: e.target.value})}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-bold text-white/30 uppercase tracking-widest ml-1">Initial Work Status</label>
                <select 
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-brand-primary appearance-none"
                  value={formData.work_status}
                  onChange={e => setFormData({...formData, work_status: e.target.value})}
                >
                  {WORK_STATUSES.map(status => (
                    <option key={status} value={status}>{status.replace('_', ' ')}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between py-6 px-10 bg-brand-primary/5 border border-brand-primary/10 rounded-3xl">
          <div className="flex items-center gap-4">
             <div className="w-10 h-10 rounded-full bg-brand-primary/20 flex items-center justify-center">
                <Truck className="w-5 h-5 text-brand-primary" />
             </div>
             <div>
                <p className="text-sm font-bold text-white">Review Driver Profile</p>
                <p className="text-[11px] text-brand-muted">Please confirm all details before submitting for onboarding.</p>
             </div>
          </div>
          <div className="flex items-center gap-4">
            <button 
              type="button" 
              onClick={() => navigate('/')}
              className="px-8 py-3 text-xs font-bold text-white/40 hover:text-white transition-colors uppercase tracking-widest"
            >
              Discard
            </button>
            <button 
              type="submit"
              disabled={loading}
              className="bg-brand-primary text-black px-12 py-3 rounded-xl font-black text-xs uppercase tracking-widest hover:brightness-110 active:scale-95 transition-all shadow-xl shadow-brand-primary/20 disabled:opacity-50"
            >
              {loading ? 'ONBOARDING...' : 'CONFIRM ONBOARDING'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
