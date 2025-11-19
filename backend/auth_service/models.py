from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from .database import Base

# Association table for User-Role many-to-many relationship
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    roles = relationship("Role", secondary=user_roles, back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    users = relationship("User", secondary=user_roles, back_populates="roles")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"
