import React from 'react';

export default function StatusBadge({ status }) {
    const map = {
        UP: { cls: 'badge-up', label: 'UP', dot: 'status-dot-up' },
        DOWN: { cls: 'badge-down', label: 'DOWN', dot: 'status-dot-down' },
        UNKNOWN: { cls: 'badge-warning', label: 'UNKNOWN', dot: 'status-dot-unknown' },
    };
    const { cls, label, dot } = map[status] || map.UNKNOWN;

    return (
        <span className={`badge ${cls} flex items-center gap-1.5`}>
            <span className={`status-dot ${dot}`} style={{ width: 8, height: 8 }}></span>
            {label}
        </span>
    );
}
