const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const { grpcServerAddress, protoPath } = require('./config')

const packageDefinition = protoLoader.loadSync(
    protoPath,
    {
        keepCase: true,
        longs: String,
        enums: String,
        defaults: true,
        oneofs: true
    });

const protoDescriptor = grpc.loadPackageDefinition(packageDefinition);
const userProto = protoDescriptor.users.UserService

const client = new userProto(grpcServerAddress, grpc.credentials.createInsecure());

module.exports = client;
