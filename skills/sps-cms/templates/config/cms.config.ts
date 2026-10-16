export interface CMSLocale {
  code: string;
  label: string;
  flag?: string;
  default?: boolean;
  rtl?: boolean;
}

export interface CMSField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'textarea' | 'rich-text' | 'image' | 'gallery' | 'boolean' | 'select' | 'date' | 'repeater';
  required?: boolean;
  localized?: boolean; // If true, stores translations per locale (e.g. en, bn, ar)
  defaultValue?: any;
  placeholder?: string;
  options?: { label: string; value: string }[];
  fields?: CMSField[]; // For nested repeater structures
}

export interface CMSCollection {
  name: string;
  label: string;
  icon?: string;
  slugPrefix?: string;
  fields: CMSField[];
  supportsHomepageToggle?: boolean;
  supportsFeatured?: boolean;
}

export interface CMSConfig {
  siteTitle: string;
  defaultLocale: string;
  locales: CMSLocale[];
  database: 'mysql' | 'postgres' | 'sqlite' | 'd1' | 'libsql';
  mediaStorage: 'local' | 'r2' | 's3';
  mediaUploadDir: string;
  collections: CMSCollection[];
}

/**
 * Universal SPS-CMS Multi-Language (i18n) Configuration
 * Supports English, Bengali, Arabic (RTL), and any other languages.
 */
export const cmsConfig: CMSConfig = {
  siteTitle: "Client Management Portal",
  defaultLocale: "en",
  locales: [
    { code: "en", label: "English", flag: "🇺🇸", default: true },
    { code: "bn", label: "বাংলা", flag: "🇧🇩" },
    { code: "ar", label: "العربية", flag: "🇸🇦", rtl: true }
  ],
  database: "mysql",
  mediaStorage: "local",
  mediaUploadDir: "public/uploads",
  collections: [
    // Tour Packages with Multi-Language Fields
    {
      name: "packages",
      label: "Tour Packages",
      icon: "Plane",
      slugPrefix: "packages",
      supportsHomepageToggle: true,
      supportsFeatured: true,
      fields: [
        { name: "title", label: "Package Title", type: "text", required: true, localized: true },
        { name: "price", label: "Price ($)", type: "number", required: true },
        { name: "duration", label: "Duration (e.g. 5 Days)", type: "text", required: true, localized: true },
        { name: "featured_image", label: "Featured Image", type: "image", required: true },
        { name: "gallery", label: "Gallery Photos", type: "gallery" },
        { name: "description", label: "Tour Overview", type: "rich-text", localized: true },
        {
          name: "itinerary",
          label: "Day-by-Day Itinerary",
          type: "repeater",
          localized: true,
          fields: [
            { name: "day_title", label: "Day Heading", type: "text" },
            { name: "day_details", label: "Activities & Details", type: "textarea" }
          ]
        }
      ]
    }
  ]
};
