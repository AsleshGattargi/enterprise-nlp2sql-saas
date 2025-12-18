from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, Enum, Boolean, JSON, ForeignKey, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum as PyEnum

Base = declarative_base()

class Organization(Base):
    __tablename__ = "organizations"
    
    org_id = Column(String(36), primary_key=True)
    org_name = Column(String(100), nullable=False)
    domain = Column(String(100), nullable=False, unique=True)
    database_type = Column(Enum('mysql', 'postgresql', 'mongodb', 'sqlite'), nullable=False)
    database_name = Column(String(100), nullable=False)
    industry = Column(String(50))
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)
    
    users = relationship("User", back_populates="organization")

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(36), primary_key=True)
    org_id = Column(String(36), ForeignKey('organizations.org_id'), nullable=False)
    username = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    department = Column(String(50))
    role = Column(Enum('admin', 'manager', 'analyst', 'developer', 'viewer'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)
    
    organization = relationship("Organization", back_populates="users")
    permissions = relationship("UserPermission", back_populates="user")
    hdt_assignment = relationship("UserHDTAssignment", back_populates="user", uselist=False)

class HumanDigitalTwin(Base):
    __tablename__ = "human_digital_twins"
    
    hdt_id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    context = Column(Text)
    skillset = Column(JSON)
    languages = Column(JSON)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)
    
    agents = relationship("HDTAgent", back_populates="hdt")
    user_assignments = relationship("UserHDTAssignment", back_populates="hdt")

class Agent(Base):
    __tablename__ = "agents"
    
    agent_id = Column(String(36), primary_key=True)
    agent_name = Column(String(100), nullable=False)
    agent_type = Column(Enum('nlp2sql', 'rag', 'analytics', 'reporting', 'chatbot'), nullable=False)
    description = Column(Text)
    capabilities = Column(JSON)
    config = Column(JSON)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)
    
    hdts = relationship("HDTAgent", back_populates="agent")

class HDTAgent(Base):
    __tablename__ = "hdt_agents"
    
    hdt_id = Column(String(36), ForeignKey('human_digital_twins.hdt_id'), primary_key=True)
    agent_id = Column(String(36), ForeignKey('agents.agent_id'), primary_key=True)
    
    hdt = relationship("HumanDigitalTwin", back_populates="agents")
    agent = relationship("Agent", back_populates="hdts")

class UserHDTAssignment(Base):
    __tablename__ = "user_hdt_assignments"
    
    user_id = Column(String(36), ForeignKey('users.user_id'), primary_key=True)
    hdt_id = Column(String(36), ForeignKey('human_digital_twins.hdt_id'), nullable=False)
    assigned_at = Column(TIMESTAMP, nullable=False)
    
    user = relationship("User", back_populates="hdt_assignment")
    hdt = relationship("HumanDigitalTwin", back_populates="user_assignments")

class UserPermission(Base):
    __tablename__ = "user_permissions"
    
    permission_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_name = Column(String(100), nullable=False)
    access_level = Column(Enum('read', 'write', 'admin'), nullable=False)
    
    user = relationship("User", back_populates="permissions")

class QueryLog(Base):
    __tablename__ = "query_log"
    
    log_id = Column(String(36), primary_key=True)
    org_id = Column(String(36), ForeignKey('organizations.org_id'), nullable=False)
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    query_text = Column(Text, nullable=False)
    generated_sql = Column(Text)
    query_type = Column(String(50))
    execution_status = Column(Enum('success', 'error', 'blocked'), nullable=False)
    execution_time_ms = Column(Integer)
    error_message = Column(Text)
    timestamp = Column(TIMESTAMP, nullable=False)

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    session_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)

# Pydantic Models for API
class UserRole(PyEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    DEVELOPER = "developer"
    VIEWER = "viewer"

class AgentType(PyEnum):
    NLP2SQL = "nlp2sql"
    RAG = "rag"
    ANALYTICS = "analytics"
    REPORTING = "reporting"
    CHATBOT = "chatbot"

class DatabaseType(PyEnum):
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    SQLITE = "sqlite"

class AccessLevel(PyEnum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class OrganizationResponse(BaseModel):
    org_id: str
    org_name: str
    domain: str
    database_type: str
    database_name: str
    industry: Optional[str]

class UserResponse(BaseModel):
    user_id: str
    org_id: str
    username: str
    email: str
    full_name: Optional[str]
    department: Optional[str]
    role: str
    is_active: bool

class HDTResponse(BaseModel):
    hdt_id: str
    name: str
    description: Optional[str]
    context: Optional[str]
    skillset: List[str]
    languages: List[str]
    agents: List[str]

class AgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    agent_type: str
    description: Optional[str]
    capabilities: List[str]
    config: Dict[str, Any]

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    organization: OrganizationResponse
    hdt: Optional[HDTResponse]

class QueryRequest(BaseModel):
    query_text: str
    export_format: Optional[str] = None

class QueryResponse(BaseModel):
    query_id: str
    generated_sql: Optional[str]
    results: List[Dict[str, Any]]
    execution_time_ms: int
    status: str
    message: Optional[str]
    export_url: Optional[str]

class PermissionCheck(BaseModel):
    resource_type: str
    resource_name: str
    access_level: str
    has_permission: bool

class UserPermissionResponse(BaseModel):
    user_id: str
    permissions: List[PermissionCheck]