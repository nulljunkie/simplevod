# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: users.proto
# Protobuf Python Version: 5.28.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    28,
    1,
    '',
    'users.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0busers.proto\x12\x05users\"&\n\x15GetUserByEmailRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\"d\n\x16GetUserByEmailResponse\x12\x0f\n\x07user_id\x18\x01 \x01(\x05\x12\r\n\x05\x65mail\x18\x02 \x01(\t\x12\x17\n\x0fhashed_password\x18\x03 \x01(\t\x12\x11\n\tis_active\x18\x04 \x01(\x08\"4\n\x11\x43reateUserRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\"6\n\x12\x43reateUserResponse\x12\x0f\n\x07user_id\x18\x01 \x01(\x05\x12\x0f\n\x07message\x18\x02 \x01(\t\"$\n\x13\x41\x63tivateUserRequest\x12\r\n\x05token\x18\x01 \x01(\t\"8\n\x14\x41\x63tivateUserResponse\x12\x0f\n\x07user_id\x18\x01 \x01(\x05\x12\x0f\n\x07message\x18\x02 \x01(\t2\xe8\x01\n\x0bUserService\x12M\n\x0eGetUserByEmail\x12\x1c.users.GetUserByEmailRequest\x1a\x1d.users.GetUserByEmailResponse\x12\x41\n\nCreateUser\x12\x18.users.CreateUserRequest\x1a\x19.users.CreateUserResponse\x12G\n\x0c\x41\x63tivateUser\x12\x1a.users.ActivateUserRequest\x1a\x1b.users.ActivateUserResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'users_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_GETUSERBYEMAILREQUEST']._serialized_start=22
  _globals['_GETUSERBYEMAILREQUEST']._serialized_end=60
  _globals['_GETUSERBYEMAILRESPONSE']._serialized_start=62
  _globals['_GETUSERBYEMAILRESPONSE']._serialized_end=162
  _globals['_CREATEUSERREQUEST']._serialized_start=164
  _globals['_CREATEUSERREQUEST']._serialized_end=216
  _globals['_CREATEUSERRESPONSE']._serialized_start=218
  _globals['_CREATEUSERRESPONSE']._serialized_end=272
  _globals['_ACTIVATEUSERREQUEST']._serialized_start=274
  _globals['_ACTIVATEUSERREQUEST']._serialized_end=310
  _globals['_ACTIVATEUSERRESPONSE']._serialized_start=312
  _globals['_ACTIVATEUSERRESPONSE']._serialized_end=368
  _globals['_USERSERVICE']._serialized_start=371
  _globals['_USERSERVICE']._serialized_end=603
# @@protoc_insertion_point(module_scope)
