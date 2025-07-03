const jwt = require('jsonwebtoken');
const { errorResponse } = require('../utils/response');
const { JWT_SECRET } = require('../config/constants');
const { logger } = require('../utils/logger');

exports.protect = (req, res, next) => {
  try {
    const token = getTokenFromRequest(req);
    if (!token) return unauthorized(res, 'Not authorized to access this route');

    const decoded = verifyToken(token, res);
    if (!decoded) return;

    req.user = decoded;
    next();
  } catch (error) {
    logger.error('Auth middleware error:', error);
    return errorResponse(res, 'Server error', 500);
  }
};

exports.authorize = (...roles) => {
  return (req, res, next) => {
    if (!roles.includes(req.user.role)) {
      return errorResponse(
        res,
        `User role ${req.user.role} is not authorized to access this route`,
        403
      );
    }
    next();
  };
};


function getTokenFromRequest(req) {
  if (req.headers.authorization?.startsWith('Bearer')) {
    return req.headers.authorization.split(' ')[1];
  }
  return req.cookies?.token;
}

function verifyToken(token, res) {
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch (err) {
    logger.error('JWT verification error:', err);
    errorResponse(res, 'Not authorized to access this route', 401);
    return null;
  }
}

function unauthorized(res, message) {
  return errorResponse(res, message, 401);
}
