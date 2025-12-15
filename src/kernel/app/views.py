from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


from .forms import PhoneLookupForm
from .services import get_num_info, NumberNotFound, NumberNotRecognized


def phone_lookup_view(request: HttpRequest) -> HttpResponse:
    result = None
    error = None

    if request.method == "POST":
        form = PhoneLookupForm(request.POST)
        if form.is_valid():
            number = form.cleaned_data["number"]
            try:
                result = get_num_info(number)
            except (NumberNotFound, NumberNotRecognized) as exc:
                error = str(exc)
    else:
        form = PhoneLookupForm()

    context = {
        "form": form,
        "result": result,
        "error": error,
    }
    return render(request, "main.html", context)

