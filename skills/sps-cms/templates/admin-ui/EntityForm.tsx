import React, { useState } from 'react';
import { CMSCollection, CMSField } from '../config/cms.config';
import { MediaUploader } from './MediaUploader';

interface EntityFormProps {
  collection: CMSCollection;
  initialData?: any;
  onSubmit: (formData: any) => Promise<void>;
  onCancel: () => void;
}

export const EntityForm: React.FC<EntityFormProps> = ({ collection, initialData, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState<any>(() => {
    if (initialData) return initialData;
    const defaults: any = {
      title: '',
      slug: '',
      price: '',
      status: 'published',
      show_on_homepage: true,
      is_featured: false,
      featured_image: '',
      data: {}
    };
    return defaults;
  });

  const [saving, setSaving] = useState(false);

  // Auto slug generator
  const handleTitleChange = (val: string) => {
    const updated = { ...formData, title: val };
    if (!initialData || !formData.slug) {
      updated.slug = val
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/(^-|-$)+/g, '');
    }
    setFormData(updated);
  };

  const handleFieldChange = (fieldName: string, val: any) => {
    setFormData({
      ...formData,
      data: {
        ...formData.data,
        [fieldName]: val
      }
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSubmit(formData);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Top action bar */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
          >
            ← Back to {collection.label}
          </button>
          <h2 className="text-xl font-bold text-white">
            {initialData ? `Edit ${collection.label.slice(0, -1)}: ${initialData.title}` : `Create New ${collection.label.slice(0, -1)}`}
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={saving}
            className="px-5 py-2 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-semibold rounded-lg text-sm transition-all shadow-lg shadow-emerald-500/20"
          >
            {saving ? 'Saving...' : '🚀 Save & Publish'}
          </button>
        </div>
      </div>

      {/* Two Column Layout (Shopify Inspired) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Main Fields */}
        <div className="lg:col-span-2 space-y-6">
          {/* Title & Slug Box */}
          <div className="bg-slate-950 p-6 rounded-xl border border-slate-800 space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Title / Name *
              </label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => handleTitleChange(e.target.value)}
                placeholder="e.g. Bali 5-Day Tropical Escape"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white font-medium focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                URL Slug (Auto-generated) *
              </label>
              <div className="flex items-center bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 font-mono text-sm text-slate-400">
                <span>/{collection.slugPrefix || collection.name}/</span>
                <input
                  type="text"
                  required
                  value={formData.slug}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                  className="bg-transparent text-white focus:outline-none w-full ml-1"
                />
              </div>
            </div>
          </div>

          {/* Dynamic Collection Fields */}
          <div className="bg-slate-950 p-6 rounded-xl border border-slate-800 space-y-5">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800 pb-2">
              Details & Content
            </h3>

            {collection.fields.map((field) => {
              if (field.name === 'title' || field.name === 'featured_image') return null;

              if (field.type === 'number') {
                return (
                  <div key={field.name}>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">{field.label}</label>
                    <input
                      type="number"
                      value={field.name === 'price' ? formData.price : (formData.data[field.name] || '')}
                      onChange={(e) => {
                        if (field.name === 'price') {
                          setFormData({ ...formData, price: e.target.value });
                        } else {
                          handleFieldChange(field.name, e.target.value);
                        }
                      }}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                );
              }

              if (field.type === 'textarea' || field.type === 'rich-text') {
                return (
                  <div key={field.name}>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">{field.label}</label>
                    <textarea
                      rows={4}
                      value={formData.data[field.name] || ''}
                      onChange={(e) => handleFieldChange(field.name, e.target.value)}
                      placeholder={field.placeholder}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                );
              }

              if (field.type === 'repeater') {
                const items = formData.data[field.name] || [];
                return (
                  <div key={field.name} className="border border-slate-800 rounded-xl p-4 bg-slate-900/40 space-y-3">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-semibold uppercase tracking-wider text-emerald-400">{field.label}</label>
                      <button
                        type="button"
                        onClick={() => handleFieldChange(field.name, [...items, {}])}
                        className="text-xs px-2 py-1 bg-emerald-500/20 text-emerald-300 rounded border border-emerald-500/30"
                      >
                        + Add Item
                      </button>
                    </div>
                    {items.map((item: any, idx: number) => (
                      <div key={idx} className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-2 relative">
                        <button
                          type="button"
                          onClick={() => {
                            const updated = items.filter((_: any, i: number) => i !== idx);
                            handleFieldChange(field.name, updated);
                          }}
                          className="absolute top-2 right-2 text-xs text-rose-400 hover:underline"
                        >
                          Remove
                        </button>
                        {field.fields?.map((nested) => (
                          <div key={nested.name}>
                            <label className="text-[11px] text-slate-400">{nested.label}</label>
                            <input
                              type="text"
                              value={item[nested.name] || ''}
                              onChange={(e) => {
                                const newItems = [...items];
                                newItems[idx] = { ...newItems[idx], [nested.name]: e.target.value };
                                handleFieldChange(field.name, newItems);
                              }}
                              className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1 text-sm text-white focus:outline-none focus:border-emerald-500"
                            />
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                );
              }

              return (
                <div key={field.name}>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">{field.label}</label>
                  <input
                    type="text"
                    value={formData.data[field.name] || ''}
                    onChange={(e) => handleFieldChange(field.name, e.target.value)}
                    placeholder={field.placeholder}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Inspector Sidebar */}
        <div className="space-y-6">
          {/* Status & Visibility */}
          <div className="bg-slate-950 p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800 pb-2">
              Visibility & Publishing
            </h3>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="published">Published (Live)</option>
                <option value="draft">Draft (Hidden)</option>
                <option value="archived">Archived</option>
              </select>
            </div>

            {collection.supportsHomepageToggle && (
              <label className="flex items-center gap-2.5 cursor-pointer pt-2">
                <input
                  type="checkbox"
                  checked={formData.show_on_homepage}
                  onChange={(e) => setFormData({ ...formData, show_on_homepage: e.target.checked })}
                  className="rounded bg-slate-900 border-slate-700 text-emerald-500 focus:ring-0"
                />
                <span className="text-xs font-medium text-slate-200">Show in Homepage Featured Grid</span>
              </label>
            )}

            {collection.supportsFeatured && (
              <label className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_featured}
                  onChange={(e) => setFormData({ ...formData, is_featured: e.target.checked })}
                  className="rounded bg-slate-900 border-slate-700 text-emerald-500 focus:ring-0"
                />
                <span className="text-xs font-medium text-slate-200">Mark as Trending / VIP</span>
              </label>
            )}
          </div>

          {/* Featured Image Uploader */}
          <div className="bg-slate-950 p-6 rounded-xl border border-slate-800 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800 pb-2">
              Featured Image
            </h3>
            <MediaUploader
              value={formData.featured_image}
              onChange={(url) => setFormData({ ...formData, featured_image: url })}
            />
          </div>
        </div>
      </div>
    </form>
  );
};
