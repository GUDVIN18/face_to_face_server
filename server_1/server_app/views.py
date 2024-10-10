from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
from server_app.models import ServerConfig, Process
from AI_models.inswapper.swapper import start
from datetime import datetime
import requests
import traceback
import multiprocessing
from django.core.files import File
from django.core.files.base import ContentFile
import os


@csrf_exempt  
def get_data(request):
    if request.method == "POST":
        if request.FILES.get("file"):
            server_auth_token = request.POST.get("server_auth_token")
            try:
                if ServerConfig.objects.first().auth_token == server_auth_token:
                    print(f'{request.POST}\n\n')
                    # server_address = request.POST.get("server_address")
                    # server_name = request.POST.get("server_name")
                    # server_port = request.POST.get("server_port")
                    server_max_process = request.POST.get("server_max_process")
                    # user_tg_id = request.POST.get("user_tg_id") #
                    process_backend_id = request.POST.get("process_backend_id") #
                    task_id = request.POST.get("task_id")
                    # emoji = request.POST.get("emoji")
                    # original_photo_id = request.POST.get("original_photo_id")
                    # print(original_photo_id)

                    inswapper_config_upscale = int(request.POST.get("inswapper_config_upscale"))
                    inswapper_config_codeformer_fidelity = float(request.POST.get("inswapper_config_codeformer_fidelity"))


                    file = request.FILES.get("file")
                    target_file = request.FILES.get("target_file")


                    process_start = Process.objects.filter(process_ended=False)
                    print(f'--------ЗАПУЩЕННЫЕ ПРОЦЕССЫ {process_start}----------')
                    
                    if not process_start.exists() or len(process_start) < int(server_max_process):
                        

                        process_create = Process.objects.create(
                            process_backend_id = process_backend_id,
                            inswapper_config_upscale = inswapper_config_upscale,
                            inswapper_config_codeformer_fidelity = inswapper_config_codeformer_fidelity,
                            process_started = False,
                            maximum_number_processes = server_max_process,
                            # original_photo_id = original_photo_id,
                            # emoji = emoji,
                        )

                        print(f'--------ПРОЦЕСС СОЗДАН {process_create.id}----------')
                        
                        if process_create:
                            try:
                                url = f"http://141.105.71.236:8585/get_task_status"
                                data = {
                                    "task_status": 'ACCEPTED',
                                    "id": task_id,
                                }
                                requests.post(url, data=data)

                                src = f"/home/dmitriy/SD/face_to_face_server/face_to_face_server_1/server_1/media/{file.name}"

                                update_process = Process.objects.get(id=process_create.id)

                                update_process.source_img.save(file.name, file)
                                print('target_file.name', target_file.name)
                                update_process.target_img.save(target_file.name, target_file)

                                output_filename = f"output_{file.name}"
                                update_process.output_img.save(output_filename, ContentFile(b''), save=False)

                                update_process.task_id = task_id
                                update_process.save()


                                return HttpResponse(json.dumps({f"success": f"{ServerConfig.objects.first().config_title} WORKER START"}), status=200)

        
                            except Exception as e:
                                process = Process.objects.get(id=process_create.id)
                                if process:
                                    process.process_error = str(e)
                                    process.process_error_traceback = traceback.format_exc()
                                    process.save() 
                                return HttpResponse(json.dumps({f"error": f"Exception as"}), status=200)
                        else:
                            print(f'--------ПРОЦЕСС НЕ СОЗДАН----------')
                            return HttpResponse(f"Not Created {ServerConfig.objects.first().config_title}")
                    else:
                        return HttpResponse(f"MAX Proccess {ServerConfig.objects.first().config_title}")
                else:
                    return HttpResponse(f"Invalid Token {ServerConfig.objects.first().config_title}")
            except Exception as e:
                print(f'Error {ServerConfig.objects.first().config_title}', e)
                return HttpResponse(json.dumps({"error": f"Access error > {e}"}), status=500)
        else:
            print('error non file')
            return HttpResponse(json.dumps({"error": "500"}), status=500)
    else:
        print(request.method)
        return HttpResponse(f"Ошибка запроса {ServerConfig.objects.first().config_title}")