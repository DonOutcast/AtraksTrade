from django.http import JsonResponse, HttpRequest
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import api_view

from app.exceptions import NumberNotRecognized, NumberNotFound
from app.services import get_num_info


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="number",
            description="Номер телефона в формате MSISDN (например, 79173453223)",
            required=True,
            type=str,
        ),
    ],
    responses={
        200: {
            "type": "object",
            "properties": {
                "number": {"type": "string"},
                "operator": {"type": "string"},
                "region": {"type": "string"},
            },
        },
        400: {"description": "Некорректный номер"},
        404: {"description": "Номер не найден"},
    },
)
@api_view(["GET"])
def api_phone_info(request: HttpRequest) -> JsonResponse:
    number = request.GET.get("number")

    if not number:
        return JsonResponse(
            {"detail": 'Параметр "number" обязателен'},
            status=400,
        )

    try:
        data = get_num_info(number)
    except NumberNotRecognized as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    except NumberNotFound as exc:
        return JsonResponse({"detail": str(exc)}, status=404)

    return JsonResponse(data, status=200)
