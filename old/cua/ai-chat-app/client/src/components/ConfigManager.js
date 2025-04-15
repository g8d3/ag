import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ConfigManager({ userId }) {
  const [configs, setConfigs] = useState([]);
  const [name, setName] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [modelId, setModelId] = useState('');

  useEffect(() => {
    axios.get(`http://localhost:5000/config?userId=${userId}`).then((res) => setConfigs(res.data));
  }, [userId]);

  const saveConfig = async () => {
    await axios.post('http://localhost:5000/config', { userId, name, baseUrl, apiKey, modelId });
    const res = await axios.get(`http://localhost:5000/config?userId=${userId}`);
    setConfigs(res.data);
  };

  const selectConfig = (config) => {
    setBaseUrl(config.baseUrl);
    setApiKey(config.apiKey);
    setModelId(config.modelId);
  };

  return (
    <div id="config-tab">
      <h2>Configurations</h2>
      <input id="config-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Config Name" />
      <input id="base-url" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} placeholder="Base URL" />
      <input id="api-key" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="API Key" />
      <input id="model-id" value={modelId} onChange={(e) => setModelId(e.target.value)} placeholder="Model ID" />
      <button id="save-config" onClick={saveConfig}>Save Config</button>
      <ul id="config-list">
        {configs.map((config) => (
          <li key={config.id} onClick={() => selectConfig(config)}>{config.name}</li>
        ))}
      </ul>
    </div>
  );
}

export default ConfigManager;