import React, { useState } from 'react';

interface MediaUploaderProps {
  value?: string;
  onChange: (url: string) => void;
}

export const MediaUploader: React.FC<MediaUploaderProps> = ({ value, onChange }) => {
  const [uploading, setUploading] = useState(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.url) {
        onChange(data.url);
      }
    } catch (err) {
      console.error('Upload failed:', err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-3">
      {value ? (
        <div className="relative group rounded-xl overflow-hidden border border-slate-800 bg-slate-900">
          <img src={value} alt="Preview" className="w-full h-40 object-cover" />
          <div className="absolute inset-0 bg-slate-950/70 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
            <button
              type="button"
              onClick={() => onChange('')}
              className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded text-xs font-semibold"
            >
              Remove
            </button>
          </div>
        </div>
      ) : (
        <label className="border-2 border-dashed border-slate-800 hover:border-emerald-500/50 bg-slate-900/50 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-colors group">
          <div className="w-10 h-10 rounded-full bg-slate-800 group-hover:bg-emerald-500/10 flex items-center justify-center text-slate-400 group-hover:text-emerald-400 mb-2">
            📷
          </div>
          <span className="text-xs font-medium text-slate-300">
            {uploading ? 'Uploading to /public/uploads...' : 'Click to Upload or Drag & Drop'}
          </span>
          <span className="text-[11px] text-slate-500 mt-1">PNG, JPG, WEBP up to 10MB</span>
          <input
            type="file"
            accept="image/*"
            disabled={uploading}
            onChange={handleFileChange}
            className="hidden"
          />
        </label>
      )}
    </div>
  );
};
