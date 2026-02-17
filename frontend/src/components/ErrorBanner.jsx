import React from 'react';

export default function ErrorBanner({ message, onRetry }) {
    return (
        <div className="mx-auto max-w-lg animate-slide-up">
            <div className="glass-card border-red-500/30 p-6 text-center">
                <div className="text-3xl mb-3">⚠️</div>
                <h3 className="text-lg font-semibold text-red-400 mb-1">Something went wrong</h3>
                <p className="text-sm text-surface-200 mb-4">{message}</p>
                {onRetry && (
                    <button
                        onClick={onRetry}
                        className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium transition-colors duration-200"
                    >
                        Retry
                    </button>
                )}
            </div>
        </div>
    );
}
