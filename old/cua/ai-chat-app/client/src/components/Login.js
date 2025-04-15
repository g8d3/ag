import React, { useState } from 'react';
import axios from 'axios';

function Login({ setToken, setUserId }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    try {
      const res = await axios.post('http://localhost:5000/auth/login', { username, password });
      setToken(res.data.token);
      setUserId(username); // Simplified; use real userId from JWT if needed
    } catch (err) {
      alert('Login failed');
    }
  };

  const handleRegister = async () => {
    try {
      await axios.post('http://localhost:5000/auth/register', { username, password });
      alert('Registered! Please login.');
    } catch (err) {
      alert('Registration failed');
    }
  };

  return (
    <div className="login">
      <input id="username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
      <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
      <button id="login-button" onClick={handleLogin}>Login</button>
      <button onClick={handleRegister}>Register</button>
    </div>
  );
}

export default Login;