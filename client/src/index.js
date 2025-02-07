import React from 'react';
import ReactDOM from 'react-dom/client'; // Note the change here
import './index.css'; // Optional: if you have global styles
import App from './App'; // Import your App component

// Create a root and render the App component
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
