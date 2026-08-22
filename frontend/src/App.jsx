import React, { useState, useEffect } from 'react';
import Dashboard from './pages/Dashboard';
import OptimizerPage from './pages/OptimizerPage';
import AssessmentPage from './pages/AssessmentPage';
import ReviewQueue from './pages/ReviewQueue';
import OrderDetail from './pages/OrderDetail';
import { fetchMetrics } from './api/client';
import { 
  LayoutDashboard, 
  SlidersHorizontal, 
  Activity, 
  ListChecks, 
  ShieldCheck, 
  AlertCircle, 
  RefreshCw,
  Building2,
  ChevronRight
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedOrderId, setSelectedOrderId] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loadingMetrics, setLoadingMetrics] = useState(true);
  const [metricsError, setMetricsError] = useState(null);

  const loadMetrics = async () => {
    setLoadingMetrics(true);
    setMetricsError(null);
    try {
      const data = await fetchMetrics();
      setMetrics(data);
    } catch (err) {
      setMetricsError(err.message || 'Could not connect to risk engine backend');
    } finally {
      setLoadingMetrics(false);
    }
  };

  useEffect(() => { loadMetrics(); }, []);

  const handleSelectOrder = (orderId) => {
    setSelectedOrderId(orderId);
    setActiveTab('detail');
  };

  const NAV_ITEMS = [
    { id: 'dashboard', label: 'Executive Dashboard', icon: LayoutDashboard },
    { id: 'optimizer', label: 'Threshold Optimizer', icon: SlidersHorizontal },
    { id: 'assessment', label: 'Risk Assessment', icon: Activity },
    { id: 'queue', label: 'Audit Review Queue', icon: ListChecks },
  ];

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800 flex flex-col md:flex-row" style={{ fontFamily: "'Inter', sans-serif" }}>

      {/* LEFT SIDEBAR NAVIGATION */}
      <aside className="w-full md:w-64 bg-slate-900 text-white flex-shrink-0 border-r border-slate-800 flex flex-col justify-between shadow-lg">
        <div>
          {/* Bank Brand Header */}
          <div className="p-5 border-b border-slate-800 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-blue-600 text-white shadow-md">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <div className="font-bold text-base tracking-tight text-white leading-tight">
                ApexRisk
              </div>
              <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider mt-0.5">
                Enterprise Risk Portal
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            <div className="px-3 pt-3 pb-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
              Navigation Menu
            </div>
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id || (item.id === 'queue' && activeTab === 'detail');
              return (
                <button
                  key={item.id}
                  onClick={() => { setActiveTab(item.id); setSelectedOrderId(null); }}
                  className={`w-full flex items-center justify-between px-3.5 py-3 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-md font-bold'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {isActive && <ChevronRight className="w-3.5 h-3.5 text-blue-200" />}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer - System Health */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/40">
          <div className="flex items-center gap-2.5">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <div>
              <div className="text-xs font-semibold text-slate-300">Risk Engine Live</div>
              <div className="text-[10px] text-slate-500 font-mono">Status: Operational</div>
            </div>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Bar */}
        <header className="bg-white border-b border-slate-200 px-6 py-4 shadow-sm flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-slate-800">
              {activeTab === 'dashboard' && 'Executive Risk Dashboard'}
              {activeTab === 'optimizer' && 'Financial Threshold Optimizer'}
              {activeTab === 'assessment' && 'Transaction Risk Assessment'}
              {activeTab === 'queue' && 'Audit Review Queue'}
              {activeTab === 'detail' && 'Transaction Audit Record'}
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Secure Corporate Risk Management Console
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 px-3 py-1.5 rounded-md border border-slate-200">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span className="font-semibold text-slate-700">Bank Security Level: High</span>
          </div>
        </header>

        {/* Content Body */}
        <main className="p-6 md:p-8 flex-1 max-w-7xl w-full mx-auto">
          {loadingMetrics ? (
            <div className="flex flex-col items-center justify-center py-28 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin mb-3 text-blue-600" />
              <p className="text-sm font-semibold text-slate-600">Connecting to ApexRisk Engine...</p>
            </div>
          ) : metricsError ? (
            <div className="bg-white border border-red-200 rounded-xl p-8 max-w-xl mx-auto text-center shadow-sm">
              <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
              <h3 className="text-lg font-bold text-slate-800 mb-2">Backend Connection Required</h3>
              <p className="text-sm text-slate-500 mb-6">{metricsError}</p>
              <button
                onClick={loadMetrics}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition"
              >
                Retry Connection
              </button>
            </div>
          ) : (
            <>
              {activeTab === 'dashboard' && <Dashboard metrics={metrics} onNavigate={setActiveTab} />}
              {activeTab === 'optimizer' && <OptimizerPage metrics={metrics} />}
              {activeTab === 'assessment' && <AssessmentPage />}
              {activeTab === 'queue' && <ReviewQueue onSelectOrder={handleSelectOrder} />}
              {activeTab === 'detail' && selectedOrderId && (
                <OrderDetail orderId={selectedOrderId} onBack={() => setActiveTab('queue')} />
              )}
            </>
          )}
        </main>

        {/* Corporate Footer */}
        <footer className="border-t border-slate-200 bg-white px-6 py-3 text-center text-xs text-slate-400">
          ApexRisk System · Enterprise Risk Platform · All System Operations Audited
        </footer>
      </div>
    </div>
  );
}
