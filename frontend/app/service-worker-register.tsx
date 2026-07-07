'use client';

import * as React from 'react';

export function ServiceWorkerRegister() {
  React.useEffect(() => {
    if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
      navigator.serviceWorker.register('/sw.js').catch(() => undefined);
    }
  }, []);

  return null;
}
