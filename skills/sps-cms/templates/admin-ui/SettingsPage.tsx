import React, { useState } from 'react';

interface SettingsPageProps {
  initialSettings: Record<string, string>;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ initialSettings }) => {
  const [settings, setSettings] = useState<Record<string, string>>(initialSettings);
  const [saving, setSaving] = useState(false);
  const [savedToast, setSavedToast] = useState(false);

  const handleChange = (key: string, val: string) => {
    setSettings(prev => ({ ...prev, [key]: val }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      const res = await fetch('/api/cms/save-page', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          slug: '__global__',
          content: settings
        })
      });

      if (res.ok) {
        setSavedToast(true);
        setTimeout(() => setSavedToast(false), 3000);
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8 max-w-4xl font-sans">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Site-Wide Global Settings</h2>
          <p className="text-xs text-slate-400 mt-1">
            Updating any field here immediately updates every header, footer, and contact section across the entire website.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {savedToast && (
            <span className="text-xs bg-emerald-500/20 text-emerald-300 px-3 py-1.5 rounded-full border border-emerald-500/30 font-semibold animate-fade-in">
              ✨ Global Settings Saved & Synced!
            </span>
          )}
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-bold rounded-xl text-sm transition-all shadow-lg shadow-emerald-500/20"
          >
            {saving ? 'Saving...' : '💾 Save Global Settings'}
          </button>
        </div>
      </div>

      {/* 1. General & Brand */}
      <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider text-emerald-400 border-b border-slate-800 pb-2">
          🏢 Company & Brand Information
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Company / Site Name</label>
            <input
              type="text"
              value={settings.company_name || ''}
              onChange={(e) => handleChange('company_name', e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Tagline</label>
            <input
              type="text"
              value={settings.tagline || ''}
              onChange={(e) => handleChange('tagline', e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500 text-sm"
            />
          </div>
        </div>
      </div>

      {/* 2. Contact Details */}
      <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider text-teal-400 border-b border-slate-800 pb-2">
          📞 Contact & Support (Headers, Footers & Modals)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Primary Phone Number</label>
            <input
              type="text"
              value={settings.phone || ''}
              onChange={(e) => handleChange('phone', e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-emerald-500 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">WhatsApp Number</label>
            <input
              type="text"
              value={settings.whatsapp || ''}
              onChange={(e) => handleChange('whatsapp', e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-emerald-500 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Support Email Address</label>
            <input
              type="email"
              value={settings.email || ''}
              onChange={(e) => handleChange('email', e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-emerald-500 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Physical Office Address</label>
            <input
              type="text"
              value={settings.address || ''}
              onChange={(e) => handleChange('address', e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500 text-sm"
            />
          </div>
        </div>
      </div>

      {/* 3. Social Media Links */}
      <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider text-amber-400 border-b border-slate-800 pb-2">
          🌐 Social Media Profiles
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Facebook URL</label>
            <input
              type="text"
              value={settings.facebook_url || ''}
              onChange={(e) => handleChange('facebook_url', e.target.value)}
              placeholder="https://facebook.com/..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Instagram URL</label>
            <input
              type="text"
              value={settings.instagram_url || ''}
              onChange={(e) => handleChange('instagram_url', e.target.value)}
              placeholder="https://instagram.com/..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500 text-sm"
            />
          </div>
        </div>
      </div>
    </form>
  );
};
