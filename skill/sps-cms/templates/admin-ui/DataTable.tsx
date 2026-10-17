import React, { useState } from 'react';
import { CMSCollection } from '../config/cms.config';

interface DataTableProps {
  collection: CMSCollection;
  items: any[];
  onToggleHome?: (id: number, currentVal: boolean) => void;
  onDelete?: (id: number) => void;
}

export const DataTable: React.FC<DataTableProps> = ({ collection, items, onToggleHome, onDelete }) => {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredItems = items.filter((item) => {
    const matchesSearch = item.title.toLowerCase().includes(search.toLowerCase()) ||
                          (item.slug && item.slug.toLowerCase().includes(search.toLowerCase()));
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header with Title and Add Button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">{collection.label}</h2>
          <p className="text-sm text-slate-400 mt-1">Manage and publish your {collection.label.toLowerCase()} across all pages.</p>
        </div>
        <a
          href={`/admin/collections/${collection.name}/new`}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold rounded-lg text-sm transition-all shadow-lg shadow-emerald-500/20"
        >
          <span>+</span> Add New {collection.label.slice(0, -1)}
        </a>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-slate-950/60 p-3 rounded-xl border border-slate-800">
        <div className="relative w-full sm:w-80">
          <input
            type="text"
            placeholder={`Search ${collection.label.toLowerCase()}...`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="all">All Statuses</option>
            <option value="published">Published</option>
            <option value="draft">Draft</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </div>

      {/* Table Grid */}
      <div className="bg-slate-950 rounded-xl border border-slate-800 overflow-hidden">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-900/80 text-xs uppercase font-semibold text-slate-400 border-b border-slate-800">
            <tr>
              <th className="px-4 py-3.5 w-16">Image</th>
              <th className="px-4 py-3.5">Title & Slug</th>
              {collection.fields.some(f => f.name === 'price') && (
                <th className="px-4 py-3.5">Price</th>
              )}
              {collection.supportsHomepageToggle && (
                <th className="px-4 py-3.5 text-center">Home Featured</th>
              )}
              <th className="px-4 py-3.5">Status</th>
              <th className="px-4 py-3.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filteredItems.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  No {collection.label.toLowerCase()} found. Click "+ Add New" to create one.
                </td>
              </tr>
            ) : (
              filteredItems.map((item) => (
                <tr key={item.id} className="hover:bg-slate-900/40 transition-colors">
                  <td className="px-4 py-3">
                    {item.featured_image ? (
                      <img src={item.featured_image} alt="" className="w-10 h-10 object-cover rounded-lg border border-slate-800" />
                    ) : (
                      <div className="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center text-xs text-slate-500">
                        🖼️
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 font-medium text-white">
                    <div>{item.title}</div>
                    <div className="text-xs text-slate-500 font-mono">/{collection.slugPrefix || collection.name}/{item.slug}</div>
                  </td>
                  {collection.fields.some(f => f.name === 'price') && (
                    <td className="px-4 py-3 font-semibold text-emerald-400">
                      ${item.price ?? '0'}
                    </td>
                  )}
                  {collection.supportsHomepageToggle && (
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => onToggleHome && onToggleHome(item.id, Boolean(item.show_on_homepage))}
                        className={`px-2.5 py-1 rounded-full text-xs font-semibold transition-all ${
                          item.show_on_homepage
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : 'bg-slate-800 text-slate-500 hover:text-slate-400'
                        }`}
                      >
                        {item.show_on_homepage ? 'ON (Home)' : 'OFF'}
                      </button>
                    </td>
                  )}
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium capitalize ${
                      item.status === 'published'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : 'bg-amber-950 text-amber-400 border border-amber-800'
                    }`}>
                      {item.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right space-x-2">
                    <a
                      href={`/admin/collections/${collection.name}/edit/${item.id}`}
                      className="text-xs px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded transition-colors"
                    >
                      Edit ✏️
                    </a>
                    <button
                      onClick={() => onDelete && onDelete(item.id)}
                      className="text-xs px-2.5 py-1.5 bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 rounded border border-rose-900/40 transition-colors"
                    >
                      Delete 🗑️
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
