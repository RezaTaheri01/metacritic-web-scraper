# # with below code you can start or stop bot remotely
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django_ratelimit.decorators import ratelimit
# import subprocess


# # Constants for paths and rate limiting
# BOT_SCRIPT_PATH = "/home/aghRezaScraper/scraper/scraper.py"
# PYTHON_PATH = "/home/aghRezaScraper/scraper/venv/bin/python"

# @ratelimit(key="ip", rate="1/m", block=True)
# @csrf_exempt  # Remove this if CSRF tokens can be used
# def control_bot(request):
#     if request.method != "GET":
#         return JsonResponse({"error": "Invalid request method."}, status=405)

#     action = request.GET.get("action")
#     if action not in {"start", "sssstttoop"}:
#         return JsonResponse({"error": "Invalid action."}, status=400)

#     try:
#         if action == "start":
#             if is_bot_running():
#                 return JsonResponse({"message": "Scraper is already running."}, status=200)
#             start_bots()
#             # logging.info("Bots started successfully.")
#             return JsonResponse({"message": "Scraper is started successfully."}, status=200)

#         elif action == "stop":
#             stop_bots()
#             # logging.info("Bots stopped successfully.")
#             return JsonResponse({"message": "Scraper is stopped successfully."}, status=200)

#     except Exception as e:
#         # logging.error(f"Error during bot control: {e}")
#         return JsonResponse({"error": "An error occurred."}, status=500)

# def is_bot_running():
#     result = subprocess.run(["pgrep", "-f", BOT_SCRIPT_PATH], stdout=subprocess.PIPE)
#     return bool(result.stdout)

# def start_bots():
#     subprocess.Popen([PYTHON_PATH, BOT_SCRIPT_PATH])

# def stop_bots():
#     subprocess.run(["pkill", "-f", BOT_SCRIPT_PATH])
