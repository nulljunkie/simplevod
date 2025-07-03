const secretKey = process.env.SECRET_KEY || "supersecuresecretkey";
const jwtAlgorithm = process.env.JWT_ALGORITH || "HS256";
const jwtAccessExpire = process.env.JWT_ACCESS_EXPIRE || "1h";
const grpcServerAddress = process.env.GRPC_SERVER_ADDRESS || "localhost:50051";

console.log("grpc server :", grpcServerAddress);

const protoPath = "./users.proto";

module.exports = {
  secretKey,
  jwtAlgorithm,
  jwtAccessExpire,
  grpcServerAddress,
  protoPath,
};
