
import calendar
import json
import logging

from datetime import datetime, timezone

from flask import (
    render_template,
    request,
    jsonify,
    Response,
    stream_with_context
)

from flask_login import login_required, current_user

from app.ai import ai
from app.ai.services import generate_reply_stream
from app.extensions import db
from app.models import (
    AIConversation,
    AIMessage,
    UserSubscription
)


# --------------------------------------------------
# DATE HELPERS
# --------------------------------------------------

def make_utc_aware(value):
    """Ensure a database datetime is timezone-aware."""
    if value and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value


def add_months(date_value, months):
    """Add calendar months while preserving the original day."""
    month_index = date_value.month - 1 + months
    year = date_value.year + month_index // 12
    month = month_index % 12 + 1

    day = min(
        date_value.day,
        calendar.monthrange(year, month)[1]
    )

    return date_value.replace(
        year=year,
        month=month,
        day=day
    )


# --------------------------------------------------
# SUBSCRIPTION USAGE
# --------------------------------------------------

def get_ai_usage(user_id):

    now = datetime.now(timezone.utc)

    subscriptions = (
        UserSubscription.query
        .filter_by(
            user_id=user_id,
            status="active"
        )
        .order_by(UserSubscription.starts_at.desc())
        .all()
    )

    subscription = None

    for item in subscriptions:
        starts_at = make_utc_aware(item.starts_at)
        ends_at = make_utc_aware(item.ends_at)

        if starts_at > now:
            continue

        if ends_at and ends_at <= now:
            continue

        if not item.plan or not item.plan.is_active:
            continue

        subscription = item
        break

    if not subscription:
        return None

    starts_at = make_utc_aware(subscription.starts_at)

    months_elapsed = (
        (now.year - starts_at.year) * 12
        + now.month - starts_at.month
    )

    period_start = add_months(starts_at, months_elapsed)

    if period_start > now:
        months_elapsed -= 1
        period_start = add_months(starts_at, months_elapsed)

    period_start = max(period_start, starts_at)

    messages_used = (
        AIMessage.query
        .join(AIConversation)
        .filter(
            AIConversation.user_id == user_id,
            AIMessage.role == "user",
            AIMessage.created_at >= period_start,
            AIMessage.created_at <= now
        )
        .count()
    )

    message_limit = subscription.plan.message_limit

    return {
        "plan": subscription.plan.name,
        "billing_cycle": subscription.plan.billing_cycle,
        "limit": message_limit,
        "used": messages_used,
        "remaining": max(0, message_limit - messages_used),
        "allowed": messages_used < message_limit,
        "period_start": period_start.isoformat()
    }


# --------------------------------------------------
# AI CHAT PAGE
# --------------------------------------------------

@ai.route("/")
@login_required
def chat():

    return render_template(
        "ai_chat.html",
        user=current_user,
        embedded=False
    )


# --------------------------------------------------
# EMBEDDED AI CHAT FOR HOMEPAGE
# --------------------------------------------------

@ai.route("/embedded")
@login_required
def embedded_chat():

    return render_template(
        "ai_chat.html",
        user=current_user,
        embedded=True
    )


# --------------------------------------------------
# CHECK SUBSCRIPTION USAGE
# --------------------------------------------------

@ai.route("/api/usage", methods=["GET"])
@login_required
def get_usage():

    usage = get_ai_usage(current_user.id)

    if not usage:
        return jsonify({
            "error": "You do not have an active AI subscription.",
            "subscription_required": True
        }), 403

    return jsonify({
        "usage": usage
    })


# --------------------------------------------------
# GET ALL USER CONVERSATIONS
# --------------------------------------------------

@ai.route("/api/conversations", methods=["GET"])
@login_required
def get_conversations():

    conversations = (
        AIConversation.query
        .filter_by(user_id=current_user.id)
        .order_by(AIConversation.updated_at.desc())
        .all()
    )

    return jsonify({
        "conversations": [
            {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat()
            }
            for conversation in conversations
        ]
    })


# --------------------------------------------------
# CREATE NEW CONVERSATION
# --------------------------------------------------

@ai.route("/api/conversations", methods=["POST"])
@login_required
def create_conversation():

    conversation = AIConversation(
        user_id=current_user.id,
        title="New chat"
    )

    db.session.add(conversation)
    db.session.commit()

    return jsonify({
        "id": conversation.id,
        "title": conversation.title
    }), 201


# --------------------------------------------------
# LOAD CONVERSATION MESSAGES
# --------------------------------------------------

@ai.route("/api/conversations/<int:conversation_id>", methods=["GET"])
@login_required
def get_conversation(conversation_id):

    conversation = AIConversation.query.filter_by(
        id=conversation_id,
        user_id=current_user.id
    ).first_or_404()

    return jsonify({
        "id": conversation.id,
        "title": conversation.title,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at.isoformat()
            }
            for message in conversation.messages
        ]
    })


# --------------------------------------------------
# SEND MESSAGE AND RECEIVE AI RESPONSE
# --------------------------------------------------

@ai.route("/api/chat", methods=["POST"])
@login_required
def chat_api():

    data = request.get_json(silent=True) or {}

    message = str(data.get("message", "")).strip()
    conversation_id = data.get("conversation_id")

    if not message:
        return jsonify({
            "error": "Please enter a message."
        }), 400

    if len(message) > 10000:
        return jsonify({
            "error": "Your message is too long."
        }), 400

    usage = get_ai_usage(current_user.id)

    if not usage:
        return jsonify({
            "error": "You need an active AI subscription to use MeetBook AI.",
            "subscription_required": True
        }), 403

    if not usage["allowed"]:
        return jsonify({
            "error": "You have reached your monthly AI message limit.",
            "limit_reached": True,
            "usage": usage
        }), 429

    if conversation_id is not None:

        try:
            conversation_id = int(conversation_id)

        except (ValueError, TypeError):
            return jsonify({
                "error": "Invalid conversation."
            }), 400

        conversation = AIConversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()

        if conversation is None:
            return jsonify({
                "error": "Conversation not found."
            }), 404

    else:

        conversation = AIConversation(
            user_id=current_user.id,
            title=message[:60]
        )

        db.session.add(conversation)
        db.session.flush()

    if conversation.title == "New chat":
        conversation.title = message[:60]

    previous_messages = (
        AIMessage.query
        .filter_by(conversation_id=conversation.id)
        .order_by(AIMessage.created_at.desc())
        .limit(12)
        .all()
    )

    conversation_history = [
        {
            "role": item.role,
            "content": item.content
        }
        for item in reversed(previous_messages)
    ]

    user_message = AIMessage(
        conversation_id=conversation.id,
        role="user",
        content=message
    )

    db.session.add(user_message)

    conversation.updated_at = datetime.now(timezone.utc)

    db.session.commit()

    saved_conversation_id = conversation.id

    # --------------------------------------------------
    # STREAM AI RESPONSE
    # --------------------------------------------------

    def event_stream():

        reply_parts = []

        try:

            yield (
                f"data: {json.dumps({
                    'conversation_id': saved_conversation_id,
                    'usage': usage
                })}\n\n"
            )

            for chunk in generate_reply_stream(
    message,
    conversation_history,
    user_name=current_user.full_name,
    account_type=current_user.account_type
):

                if chunk:
                    reply_parts.append(chunk)

                    yield (
                        f"data: {json.dumps({'text': chunk})}\n\n"
                    )

            full_reply = "".join(reply_parts).strip()

            if full_reply:

                assistant_message = AIMessage(
                    conversation_id=saved_conversation_id,
                    role="assistant",
                    content=full_reply
                )

                db.session.add(assistant_message)

                saved_conversation = db.session.get(
                    AIConversation,
                    saved_conversation_id
                )

                if saved_conversation:
                    saved_conversation.updated_at = (
                        datetime.now(timezone.utc)
                    )

                db.session.commit()

        except Exception:

            db.session.rollback()

            logging.exception(
                "MeetBook AI streaming request failed."
            )

            if reply_parts:

                partial_reply = "".join(reply_parts).strip()

                if partial_reply:

                    db.session.add(
                        AIMessage(
                            conversation_id=saved_conversation_id,
                            role="assistant",
                            content=partial_reply
                        )
                    )

                    db.session.commit()

            yield (
                f"data: {json.dumps({
                    'error': 'MeetBook AI could not respond. Please try again.'
                })}\n\n"
            )

        finally:

            db.session.remove()

        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
