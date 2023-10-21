import os
from multiprocessing import Process

from django.core import management
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


API_KEY = os.environ.get("BACKUP_WEBHOOK_KEY")


@csrf_exempt
@require_http_methods(["POST"])
def start_backup(request):
    if not API_KEY:
        return HttpResponseServerError()
    elif API_KEY != request.META.get("HTTP_X_API_KEY"):
        return HttpResponseForbidden()
    Process(target=management.call_command, args=('dbbackup',)).start()
    return HttpResponse("Backup started")
