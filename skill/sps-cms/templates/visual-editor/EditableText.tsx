import React from 'react';

interface EditableTextProps {
  id: string;
  defaultText: string;
  value?: string;
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'p' | 'span' | 'div';
  className?: string;
}

export const EditableText: React.FC<EditableTextProps> = ({
  id,
  defaultText,
  value,
  as: Component = 'span',
  className = ''
}) => {
  const content = value || defaultText;

  const handleInput = (e: React.FormEvent<HTMLElement>) => {
    window.dispatchEvent(new CustomEvent('sps-cms-content-changed', { detail: { id, content: e.currentTarget.innerHTML } }));
  };

  return (
    <Component
      data-sps-key={id}
      contentEditable="inherit"
      onInput={handleInput}
      suppressContentEditableWarning
      className={`sps-editable-element outline-none hover:ring-2 hover:ring-emerald-400/40 rounded transition-all ${className}`}
      dangerouslySetInnerHTML={{ __html: content }}
    />
  );
};
