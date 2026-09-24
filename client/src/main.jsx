import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import App from './App';
import { AuthProvider } from './auth';
import { ThemeProvider } from './theme';
import './styles.css';

// StrictMode intentionally omitted: it double-fires effects and would log every search twice.
createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <ThemeProvider>
      <AuthProvider><App /></AuthProvider>
      <Toaster position="top-right" toastOptions={{ style: { background: 'var(--panel)', color: 'var(--text)', border: '1px solid var(--line)' } }} />
    </ThemeProvider>
  </BrowserRouter>
);