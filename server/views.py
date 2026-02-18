from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import UserSerializer
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

from django.shortcuts import get_object_or_404

@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = get_object_or_404(User, email=email)

    if not user.check_password(password):
        return Response(
            {'detail': 'Invalid credentials'},
            status=status.HTTP_400_BAD_REQUEST
        )

    token, created = Token.objects.get_or_create(user=user)

    return Response({
        'token': token.key,
        'user': UserSerializer(user).data
    })


@api_view(['POST'])
def signup(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token = Token.objects.create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated

import requests
from django.conf import settings
@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def send_message(request):
    message = request.data.get("message")
    if not message:
        return Response(
            {"detail": "Message is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    admin_chat_id = getattr(settings, "TELEGRAM_ADMIN_CHAT_ID", None)

    if not bot_token or not admin_chat_id:
        return Response(
            {"detail": "Telegram bot token or admin chat_id not configured"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # ساخت متن پیام شامل ایمیل کاربر
    text = f"New message from {request.user.email}:\n\n{message}"

    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": admin_chat_id,
        "text": text
    }

    try:
        resp = requests.post(telegram_url, json=payload, timeout=5)
        resp.raise_for_status()  # اگر خطا بود استثنا ایجاد می‌کند
    except requests.RequestException as e:
        return Response(
            {"detail": f"Failed to send message to Telegram: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {"detail": "Message sent to Telegram successfully"},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def test_token(request):
    return Response("passed for {}".format(request.user.email))