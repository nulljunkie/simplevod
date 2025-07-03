const express = require('express');
const apiRoutes = require('./routes/apiRoutes');
const healthRoutes = require('./routes/healthRoutes');
const cors = require('cors');
const logger = require('./middleware/logger');

const app = express();

app.use(express.json());
app.use(cors());
app.use(logger);

app.use('/api', apiRoutes);
app.use(healthRoutes);

const PORT = process.env.PORT || 8100;
app.listen(PORT, () => {
  console.log(`Auth service running on port ${PORT}`);
});
