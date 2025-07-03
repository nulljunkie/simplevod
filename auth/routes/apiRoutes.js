const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { validate, userSchema, emailSchema } = require('../utils/validate');
const { secretKey, jwtAlgorithm, jwtAccessExpire } = require('../config');
const grpcClient = require('../grpcClient');
const { status: GrpcStatus } = require('@grpc/grpc-js'); // Correct import

const router = express.Router();

router.post('/register', validate(userSchema), async (req, res) => {
    const { email, password } = req.body;

    grpcClient.CreateUser({ email, password }, (error, response) => {
        if (error) {
            if (error.code === GrpcStatus.ALREADY_EXISTS) {
                return res.status(409).json({
                    success: false,
                    message: 'Email address already registered',
                    data: {}
                });
            }
            return res.status(500).json({
                success: false,
                message: error.details || 'Internal server error',
                data: {}
            });
        }

        res.json({
            success: true,
            message: response.message,
            data: { message: response.message }
        });
    });
});

router.post('/login', validate(userSchema), async (req, res) => {
    const { email, password } = req.body;

    grpcClient.GetUserByEmail({ email }, async (error, response) => {
        if (error) {
            if (error.code === GrpcStatus.NOT_FOUND) {
                return res.status(404).json({
                    success: false,
                    message: 'User not found',
                    data: {}
                });
            }
            return res.status(500).json({
                success: false,
                message: error.details || 'Internal server error',
                data: {}
            });
        }

        const isMatch = await bcrypt.compare(password, response.hashed_password);
        if (!isMatch) {
            return res.status(401).json({
                success: false,
                message: 'Invalid credentials',
                data: {}
            });
        }

        if (!response.is_active) {
            return res.status(403).json({
                success: false,
                message: 'User is not active',
                data: {}
            });
        }

        const token = jwt.sign(
            { 
                user_id: response.user_id.toString(),
                username: response.username
            },
            secretKey,
            { algorithm: jwtAlgorithm, expiresIn: jwtAccessExpire }
        );
        res.json({
            success: true,
            message: 'Login successful',
            data: { access: token }
        });
    });
});

router.get('/activate', async (req, res) => {
    const token = req.query.token;

    if (!token) {
        return res.status(400).json({
            success: false,
            message: 'Invalid activation token',
            data: {}
        });
    }

    grpcClient.ActivateUser({ token }, (error, response) => {
        if (error) {
            if (error.code === GrpcStatus.NOT_FOUND) {
                return res.status(400).json({
                    success: false,
                    message: 'Invalid activation token',
                    data: {}
                });
            }
            if (error.code === GrpcStatus.DEADLINE_EXCEEDED) {
                return res.status(410).json({
                    success: false,
                    message: 'Activation token has expired',
                    data: {}
                });
            }
            return res.status(500).json({
                success: false,
                message: error.details || 'Internal server error',
                data: {}
            });
        }

        const accessToken = jwt.sign(
            { 
                user_id: response.user_id.toString(),
                username: response.username
            },
            secretKey,
            { algorithm: jwtAlgorithm, expiresIn: jwtAccessExpire }
        );
        res.json({
            success: true,
            message: 'Account activated successfully',
            data: { access: accessToken }
        });
    });
});

router.post('/resend-activation', validate(emailSchema), async (req, res) => {
    const { email } = req.body;

    grpcClient.ResendActivationEmail({ email }, (error, response) => {
        if (error) {
            if (error.code === GrpcStatus.NOT_FOUND) {
                return res.status(404).json({
                    success: false,
                    message: 'User not found',
                    data: {}
                });
            }
            if (error.code === GrpcStatus.ALREADY_EXISTS) {
                return res.status(409).json({
                    success: false,
                    message: 'User already active',
                    data: {}
                });
            }
            return res.status(500).json({
                success: false,
                message: error.details || 'Internal server error',
                data: {}
            });
        }

        return res.json({
            success: true,
            message: response.message,
            data: { message: response.message }
        });
    });
});

module.exports = router;
