import React from 'react';

export default function LoadingSpinner({ text = 'Loading…' }) {
    return (
        <div className="flex flex-col items-center justify-center py-20 animate-fade-in">
            <div className="relative w-12 h-12 mb-4">
                <div className="absolute inset-0 rounded-full border-2 border-brand-500/20"></div>
                <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-brand-400 animate-spin"></div>
            </div>
            <p className="text-sm text-surface-200">{text}</p>
        </div>
    );
}
