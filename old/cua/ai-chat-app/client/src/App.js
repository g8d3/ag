import React, { useState } from 'react';
import Login from './components/Login';
import Chat from './components/Chat';
import ConfigManager from './components/ConfigManager';
import './styles.css';

function App() {
  const [token, setToken] = useState(null);
  const [userId, setUserId] = useState(null);

  if (!token) {
    return <Login setToken={setToken} setUserId={setUserId} />;
  }

  return (
    <div className="app">
      <ConfigManager userId={userId} />
      <Chat userId={userId} />
    </div>
  );
}

export default App;