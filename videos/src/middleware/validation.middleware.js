const { body, validationResult } = require('express-validator');
const { errorResponse } = require('../utils/response');

// Process validation results
const validate = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return errorResponse(res, errors.array().map(err => err.msg), 400);
  }
  next();
};

exports.validateVideoUpdate = [
  body('title').optional(),
  body('description').optional(),
  body('tags').optional().isArray().withMessage('Tags must be an array'),
  body('visibility')
    .optional()
    .isIn(['public', 'unlisted', 'private'])
    .withMessage('Invalid visibility value'),
  validate,
];
