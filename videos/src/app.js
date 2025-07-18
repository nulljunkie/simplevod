const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const cookieParser = require('cookie-parser');
const { errorHandler } = require('./middleware/error.middleware');
const routes = require('./routes');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());
const debugEnabled = process.env.LOG_DEBUG === 'true';
if (debugEnabled) {
  app.use(morgan('dev'));
} else {
  app.use(morgan('dev', {
    skip: function (req, res) {
      return req.originalUrl.includes('/health');
    }
  }));
}

// Routes
app.use('/api', routes);

// Error handling middleware
app.use(errorHandler);

module.exports = app;

