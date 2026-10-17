import React, { useState } from 'react';

interface Inquiry {
  id: number;
  name: string;
  email: string;
  phone: string;
  subject: string;
  message: string;
  status: 'new' | 'contacted' | 'closed';
  created_at: string;
}

interface InquiriesInboxProps {
  initialInquiries: Inquiry[];
}

export const InquiriesInbox: React.FC<InquiriesInboxProps> = ({ initialInquiries }) => {
  const [inquiries, setInquiries] = useState<Inquiry[]>(initialInquiries);
  const [selectedInquiry, setSelectedInquiry] = useState<Inquiry | null>(initialInquiries[0] || null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const filtered = inquiries.filter((inq) => {
    const matchSearch = inq.name.toLowerCase().includes(search.toLowerCase()) ||
      inq.email.toLowerCase().includes(search.toLowerCase()) ||
      inq.subject.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'all' || inq.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const handleStatusChange = async (id: number, nextStatus: 'new' | 'contacted' | 'closed') => {
    setInquiries(prev => prev.map(i => i.id === id ? { ...i, status: nextStatus } : i));
    if (selectedInquiry && selectedInquiry.id === id) {
      setSelectedInquiry({ ...selectedInquiry, status: nextStatus });
    }

    await fetch('/api/cms/inquiries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'update-status', id, status: nextStatus })
    });
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this lead inquiry?')) return;

    setInquiries(prev => prev.filter(i => i.id !== id));
    if (selectedInquiry && selectedInquiry.id === id) {
      setSelectedInquiry(null);
    }

    await fetch('/api/cms/inquiries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'delete', id })
    });
  };

  const handleExportCSV = () => {
    const headers = ['ID', 'Name', 'Email', 'Phone', 'Subject', 'Status', 'Date', 'Message'];
    const rows = inquiries.map(i => [
      i.id,
      `"${i.name}"`,
      `"${i.email}"`,
      `"${i.phone}"`,
      `"${i.subject.replace(/"/g, '""')}"`,
      i.status,
      i.created_at,
      `"${i.message.replace(/"/g, '""')}"`
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `leads_inbox_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <span>📬</span>
            <span>Client Inquiries & Leads</span>
            <span className="text-xs bg-emerald-500/20 text-emerald-300 px-2.5 py-1 rounded-full font-mono font-bold">
              {inquiries.filter(i => i.status === 'new').length} New Leads
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Zero-dependency lead capture. All submissions from booking forms and contact boxes land here automatically.
          </p>
        </div>

        <button
          onClick={handleExportCSV}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold rounded-xl text-xs flex items-center gap-1.5 transition-all self-start sm:self-auto"
        >
          <span>📥</span>
          <span>Export All Leads (CSV)</span>
        </button>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Search by customer name, email, or subject..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
        </div>
        <div className="flex gap-2">
          {['all', 'new', 'contacted', 'closed'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-2 rounded-xl text-xs font-semibold capitalize transition-colors ${
                statusFilter === st
                  ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20'
                  : 'bg-slate-950 border border-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-5 bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden divide-y divide-slate-800/60 max-h-[600px] overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              No inquiries found matching your filter.
            </div>
          ) : (
            filtered.map((inq) => (
              <div
                key={inq.id}
                onClick={() => setSelectedInquiry(inq)}
                className={`p-4 cursor-pointer transition-colors ${
                  selectedInquiry?.id === inq.id
                    ? 'bg-emerald-500/10 border-l-4 border-l-emerald-500'
                    : 'hover:bg-slate-900/60'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="font-bold text-white text-xs truncate">{inq.name}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                    inq.status === 'new'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : inq.status === 'contacted'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : 'bg-slate-800 text-slate-400'
                  }`}>
                    {inq.status}
                  </span>
                </div>
                <div className="text-[11px] font-medium text-slate-300 truncate mb-1">{inq.subject}</div>
                <div className="flex items-center justify-between text-[10px] text-slate-500">
                  <span>{inq.email}</span>
                  <span>{new Date(inq.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="lg:col-span-7 bg-slate-950 border border-slate-800 rounded-2xl p-6 space-y-6">
          {selectedInquiry ? (
            <>
              <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                  <h3 className="text-lg font-bold text-white">{selectedInquiry.name}</h3>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-1">
                    <span>📧 {selectedInquiry.email}</span>
                    {selectedInquiry.phone && <span>📞 {selectedInquiry.phone}</span>}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <select
                    value={selectedInquiry.status}
                    onChange={(e) => handleStatusChange(selectedInquiry.id, e.target.value as any)}
                    className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500 font-semibold"
                  >
                    <option value="new">Mark as: New</option>
                    <option value="contacted">Mark as: Contacted</option>
                    <option value="closed">Mark as: Closed</option>
                  </select>

                  <button
                    onClick={() => handleDelete(selectedInquiry.id)}
                    className="p-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded-lg border border-rose-500/30 text-xs"
                    title="Delete lead"
                  >
                    🗑️
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">Inquiry Subject</span>
                <div className="text-sm font-semibold text-white bg-slate-900 p-3 rounded-xl border border-slate-800">
                  {selectedInquiry.subject}
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Customer Message</span>
                <div className="text-xs text-slate-200 bg-slate-900 p-4 rounded-xl border border-slate-800 leading-relaxed whitespace-pre-wrap">
                  {selectedInquiry.message}
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center gap-3">
                <a
                  href={`mailto:${selectedInquiry.email}?subject=Re: ${encodeURIComponent(selectedInquiry.subject)}`}
                  className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl text-xs flex items-center gap-1.5 transition-all shadow-md shadow-emerald-500/20"
                >
                  <span>✉️ Reply via Email</span>
                </a>

                {selectedInquiry.phone && (
                  <a
                    href={`https://wa.me/${selectedInquiry.phone.replace(/[^0-9]/g, '')}`}
                    target="_blank"
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-emerald-400 font-semibold rounded-xl text-xs flex items-center gap-1.5 transition-all"
                  >
                    <span>💬 Open WhatsApp Chat</span>
                  </a>
                )}
              </div>
            </>
          ) : (
            <div className="p-12 text-center text-slate-500 text-xs">
              Select an inquiry from the list to view full details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
