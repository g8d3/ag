const express = require('express');
const cors = require('cors');
const authRoutes = require('./routes/auth');
const configRoutes = require('./routes/config');
const chatRoutes = require('./routes/chat');
const codeRoutes = require('./routes/code');

const app = express();
app.use(cors());
app.use(express.json());

app.use('/auth', authRoutes);
app.use('/config', configRoutes);
app.use('/chat', chatRoutes);
app.use('/code', codeRoutes);

app.listen(5000, () => console.log('Server running on http://localhost:5000'));