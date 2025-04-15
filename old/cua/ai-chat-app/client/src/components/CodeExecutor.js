import React, { useState } from 'react';
import axios from 'axios';

function CodeExecutor({ code }) {
  const [output, setOutput] = useState('');

  const runCode = async () => {
    try {
      const res = await axios.post('http://localhost:5000/code/run', { code });
      setOutput(res.data.output);
    } catch (err) {
      setOutput(err.response.data.error);
    }
  };

  return (
    <div>
      <pre><code>{code}</code></pre>
      <button id="run-code-button" onClick={runCode}>Run Code</button>
      <pre id="code-output">{output}</pre>
    </div>
  );
}

export default CodeExecutor;