const logger = (req, res, next) => {
  const ip = req.ip || req.connection.remoteAddress;
  const start = new Date();

  res.on('finish', () => {
    const timestamp = start.toLocaleString('en-US', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).replace(/,/, '');
    console.log(`${ip} - - [${timestamp}] "${req.method} ${req.originalUrl} HTTP/${req.httpVersion}" ${res.statusCode} -`);
  });

  next();
};

module.exports = logger;
