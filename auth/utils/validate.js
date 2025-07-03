const Joi = require('joi');

/**
 * Creates a validation middleware for a given Joi schema.
 * @param {Joi.Schema} schema - The Joi schema to validate against.
 * @returns {Function} Express middleware function.
 */
const validate = (schema) => {
  return (req, res, next) => {
    const { error, value } = schema.validate(req.body, {
      abortEarly: false, // Collect all validation errors
      stripUnknown: true, // Remove unknown fields
    });

    if (error) {
      const errorMessage = error.details.map((err) => err.message).join('; ');
      return res.status(400).json({
        success: false,
        message: errorMessage,
        data: {}
      });
    }

    // Sanitized data assigned to req.body
    req.body = value;
    next();
  };
};

/**
 * Joi schema for user registration and login.
 */
const userSchema = Joi.object({
  email: Joi.string()
    .email({ tlds: { allow: false } })
    .required()
    .messages({
      'string.email': 'Invalid email format',
      'any.required': 'Email is required'
    }),
  password: Joi.string()
    .min(8)
    .pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
    .required()
    .messages({
      'string.min': 'Password must be at least 8 characters long',
      'string.pattern.base': 'Password must contain at least one lowercase letter, one uppercase letter, and one digit',
      'any.required': 'Password is required'
    })
});

/**
 * Joi schema for email-only validation (e.g., resend activation).
 */
const emailSchema = Joi.object({
  email: Joi.string()
    .email({ tlds: { allow: false } })
    .required()
    .messages({
      'string.email': 'Invalid email format',
      'any.required': 'Email is required'
    })
});

module.exports = { validate, userSchema, emailSchema };
