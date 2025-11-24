from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


# ------------------------------------------------------
# B2B COMPANY MODEL
# ------------------------------------------------------
class Company(Base):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    contact_email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # All users under this company
    users = relationship("User", back_populates="company")

    # Company subscription (optional)
    subscriptions = relationship("Subscription", back_populates="company")


# ------------------------------------------------------
# USER MODEL (WORKS FOR B2C & B2B)
# ------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # user_type: free / premium / premium_pro / b2b_employee / b2b_admin
    user_type = Column(String)

    trial_status = Column(String)  # active / exhausted

    # 🔥 If user is B2B → company_id will be set
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=True)

    company = relationship("Company", back_populates="users")

    subscriptions = relationship("Subscription", back_populates="user")
    sessions = relationship("Session", back_populates="user")

# ------------------------------------------------------
# REVOKED TOKENS MODEL
# ------------------------------------------------------
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, index=True)  # JWT ID
    revoked_at = Column(DateTime, default=datetime.utcnow)


# ------------------------------------------------------
# PLAN MODEL
# ------------------------------------------------------
class Plan(Base):
    __tablename__ = "plans"

    plan_id = Column(Integer, primary_key=True, index=True)
    plan_code = Column(String, unique=True)
    sessions_per_day = Column(Integer)
    session_length_seconds = Column(Integer)
    api_requests_per_day = Column(Integer)
    metrics_included = Column(String)
    monthly_cap = Column(Integer, nullable=True)

    subscriptions = relationship("Subscription", back_populates="plan")


# ------------------------------------------------------
# SUBSCRIPTION MODEL (SUPPORTS USER OR COMPANY)
# ------------------------------------------------------
class Subscription(Base):
    __tablename__ = "subscriptions"

    subscription_id = Column(Integer, primary_key=True, index=True)

    # Either user OR company can have subscription
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=True)

    plan_id = Column(Integer, ForeignKey("plans.plan_id"))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="subscriptions")
    company = relationship("Company", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")


# ------------------------------------------------------
# SESSIONS
# ------------------------------------------------------
class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    plan_id = Column(Integer, ForeignKey("plans.plan_id"))

    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    restarts = Column(Integer, default=0)
    finalized = Column(Boolean, default=False)
    scenario_data = Column(JSON)

    user = relationship("User", back_populates="sessions")
    events = relationship("SessionEvent", back_populates="session")
    messages = relationship("Message", back_populates="session")
    transcripts = relationship("Transcript", back_populates="session")
    feedback = relationship("Feedback", uselist=False, back_populates="session")


class SessionEvent(Base):
    __tablename__ = "session_events"

    event_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.session_id"))
    event_type = Column(String)
    payload = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="events")


class Message(Base):
    __tablename__ = "messages"

    message_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.session_id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="messages")


class Transcript(Base):
    __tablename__ = "transcripts"

    transcript_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.session_id"))
    request_id = Column(String)
    transcript_text = Column(Text)
    duration_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="transcripts")


class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.session_id"))
    feedback_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="feedback")


class UsageCounter(Base):
    __tablename__ = "usage_counters"

    counter_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    date = Column(DateTime)
    sessions_count = Column(Integer)
    session_minutes = Column(Integer)
    api_requests = Column(Integer)


class RateLimitRule(Base):
    __tablename__ = "rate_limit_rules"

    rule_id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.plan_id"))
    limit_type = Column(String)   # session_day / api_day / minutes_day
    limit_value = Column(Integer)
    description = Column(Text)
