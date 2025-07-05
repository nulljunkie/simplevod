from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, UTC
import grpc
import bcrypt
import os
from sqlalchemy.exc import IntegrityError
from users_pb2 import GetUserByEmailResponse, CreateUserResponse, ActivateUserResponse, ResendActivationEmailResponse
from users_pb2_grpc import UserServiceServicer, add_UserServiceServicer_to_server
from database import ActivationToken, User, get_db, engine
from tasks import send_email_task, app as celery_app
from utils import generate_token
from decouple import config
import logging
import threading
from probe_server import ProbeState, start_probe_server

debug_enabled = os.getenv("LOG_DEBUG", "false").lower() == "true"
log_level = logging.DEBUG if debug_enabled else logging.INFO
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ACTIVATION_BASE_URL = config("ACTIVATION_BASE_URL", default="http://localhost:3000")


class UserService(UserServiceServicer):
    """
    gRPC UserService implementation for user-related operations.
    """

    def GetUserByEmail(self, request, context) -> GetUserByEmailResponse:
        """
        Retrieve a user by email address.
        Args:
            request: gRPC request containing the email.
            context: gRPC context.
        Returns:
            GetUserByEmailResponse
        """
        logger.info(f"Received GetUserByEmail request for email: {request.email}")
        with get_db() as db:
            user = db.query(User).filter_by(email=request.email).first()
            if user is not None:
                logger.info(f"User found: {user.email} (ID: {user.id})")
                return GetUserByEmailResponse(
                    user_id=user.id,
                    email=user.email,
                    username=user.username,
                    hashed_password=user.hashed_password,
                    is_active=user.is_active
                )
            else:
                logger.warning(f"User not found for email: {request.email}")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("User not found")
                return GetUserByEmailResponse()

    def CreateUser(self, request, context) -> CreateUserResponse:
        """
        Create a new user with the given email and password.
        Args:
            request: gRPC request containing email and password.
            context: gRPC context.
        Returns:
            CreateUserResponse
        """
        logger.info(f"Received CreateUser request for email: {request.email}")
        hashed_password = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt()).decode()
        
        # Extract username from email (part before @)
        base_username = request.email.split('@')[0]
        # Ensure username is valid and within length limit
        username = base_username[:50] if len(base_username) <= 50 else base_username[:50]
        
        with get_db() as db:
            try:
                # Check for username uniqueness and append number if needed
                counter = 1
                original_username = username
                while db.query(User).filter_by(username=username).first():
                    username = f"{original_username}{counter}"
                    # Ensure total length doesn't exceed 50 chars
                    if len(username) > 50:
                        username = f"{original_username[:47]}{counter}"
                    counter += 1
                
                user = User(email=request.email, username=username, hashed_password=hashed_password)
                db.add(user)
                db.commit()
                logger.info(f"User created successfully: {user.email} (ID: {user.id}, Username: {user.username})")
                token = generate_token(user.id)
                token_url = f"{ACTIVATION_BASE_URL}/activate?token={token}"
                send_email_task.delay(request.email, token_url)
                logger.info(f"Activation email sent to: {request.email}")
                context.set_code(grpc.StatusCode.OK)
                return CreateUserResponse(user_id=user.id, message="User created successfully, activation link is sent via email")
            except IntegrityError as e:
                logger.error(f"IntegrityError: Email or username already registered: {request.email}")
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details("Email address already registered")
                return CreateUserResponse(user_id=0, message="Email address already registered")
            except Exception as e:
                logger.exception(f"Unexpected error during CreateUser: {e}")
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details("Internal server error")
                return CreateUserResponse(user_id=0, message="Internal server error")

    def ActivateUser(self, request, context) -> ActivateUserResponse:
        """
        Activate a user account using an activation token.
        Args:
            request: gRPC request containing the activation token.
            context: gRPC context.
        Returns:
            ActivateUserResponse
        """
        logger.info(f"Received ActivateUser request with token: {request.token}")
        with get_db() as db:
            token = db.query(ActivationToken).filter_by(token=request.token).first()
            if token is None:
                logger.warning(f"Invalid activation token: {request.token}")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Invalid activation token")
                return ActivateUserResponse()
            if token.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
                logger.warning(f"Activation token expired: {request.token}")
                context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
                context.set_details("Activation token has expired")
                return ActivateUserResponse()
            user = db.query(User).filter_by(id=token.user_id).first()
            if user:
                user.is_active = True
                db.delete(token)
                db.commit()
                logger.info(f"User activated: {user.email} (ID: {user.id})")
                context.set_code(grpc.StatusCode.OK)
                return ActivateUserResponse(user_id=user.id, username=user.username, message="User activated successfully")
            else:
                logger.error(f"User not found for activation token: {request.token}")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("User not found for activation")
                return ActivateUserResponse()
            user.is_active = True
            db.commit()
            context.set_code(grpc.StatusCode.OK)
            return ActivateUserResponse(user_id=user.id, username=user.username, message="User is activated")

    def ResendActivationEmail(self, request, context) -> ResendActivationEmailResponse:
        """
        Resend activation email to a non-active user.
        Args:
            request: gRPC request containing the user email.
            context: gRPC context.
        Returns:
            ResendActivationEmailResponse
        """
        logger.info(f"Received ResendActivationEmail request for email: {request.email}")
        with get_db() as db:
            user = db.query(User).filter_by(email=request.email).first()
            if user is None:
                logger.warning(f"User not found for email: {request.email}")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("User not found")
                return ResendActivationEmailResponse()
            if user.is_active:
                logger.info(f"User already active: {user.email}")
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details("User already active")
                return ResendActivationEmailResponse(message="User already active")

            token = generate_token(user.id)
            token_url = f"{ACTIVATION_BASE_URL}/activate?token={token}"
            send_email_task.delay(request.email, token_url)
            logger.info(f"Activation email resent to: {request.email}")
            context.set_code(grpc.StatusCode.OK)
            return ResendActivationEmailResponse(message="Activation email resent successfully")

def serve():
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    ProbeState.readiness = True
    print("Users gRPC server running on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    start_probe_server(port=8082)
    serve()
