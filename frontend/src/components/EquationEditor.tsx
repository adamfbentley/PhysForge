import React, { useState, ChangeEvent } from 'react';

interface EquationEditorProps {
  value: string;
  onChange: (equation: string) => void;
  label?: string;
  placeholder?: string;
}

const EquationEditor: React.FC<EquationEditorProps> = ({
  value,
  onChange,
  label = 'PDE Equation',
  placeholder = 'e.g., du/dt + u*du/dx - (0.01/pi)*d2u/dx2 = 0',
}) => {
  const [cursorPosition, setCursorPosition] = useState(0);

  const handleInputChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(event.target.value);
    setCursorPosition(event.target.selectionStart);
  };

  const handleInsertSymbol = (symbol: string) => {
    const textarea = document.getElementById('equation-textarea') as HTMLTextAreaElement;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const newValue = value.substring(0, start) + symbol + value.substring(end);
    onChange(newValue);

    // Adjust cursor position after insertion
    const newCursorPosition = start + symbol.length;
    setCursorPosition(newCursorPosition);
    // Use setTimeout to ensure the DOM updates before setting selectionRange
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(newCursorPosition, newCursorPosition);
    }, 0);
  };

  return (
    <div className="mb-4">
      <label htmlFor="equation-textarea" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        {label}
      </label>
      <div className="relative">
        <textarea
          id="equation-textarea"
          rows={5}
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm
                     dark:bg-gray-800 dark:border-gray-600 dark:text-white dark:focus:border-blue-500 dark:focus:ring-blue-500"
          value={value}
          onChange={handleInputChange}
          placeholder={placeholder}
          onSelect={(e) => setCursorPosition(e.currentTarget.selectionStart)}
          onKeyUp={(e) => setCursorPosition(e.currentTarget.selectionStart)}
          onClick={(e) => setCursorPosition(e.currentTarget.selectionStart)}
        />
        <div className="mt-2 flex flex-wrap gap-2">
          <button type="button" onClick={() => handleInsertSymbol('∂')} className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600">∂</button>
          <button type="button" onClick={() => handleInsertSymbol('²')} className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600">²</button>
          <button type="button" onClick={() => handleInsertSymbol('³')} className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600">³</button>
          <button type="button" onClick={() => handleInsertSymbol('+')} className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600">+</button>
          <button type="button" onClick={() => handleInsertSymbol('-')} className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600">-</button>
          <button type="button" onClick={() => handleInsertSymbol('*')} className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600">*</button>
          <button type="button" onClick={() => handleInsertSymbol('/')} className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600">/</button>
          <button type="button" onClick={() => handleInsertSymbol('=')} className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600">=</button>
          <button type="button" onClick={() => handleInsertSymbol('sin()')} className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600">sin</button>
          <button type="button" onClick={() => handleInsertSymbol('cos()')} className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600">cos</button>
          <button type="button" onClick={() => handleInsertSymbol('exp()')} className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600">exp</button>
          <button type="button" onClick={() => handleInsertSymbol('log()')} className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600">log</button>
        </div>
      </div>
    </div>
  );
};

export default EquationEditor;
