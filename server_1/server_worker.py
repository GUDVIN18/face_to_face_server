import multiprocessing
import time
from datetime import datetime
import requests
from django.db import transaction
import os
from multiprocessing import get_context
import os
import django



def process_task(process_id):
    # Установите переменную окружения с настройками вашего проекта
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server_1.settings')

    # Настройка Django
    django.setup()

    from server_app.models import Process
    from AI_models.inswapper.swapper import start
    
    print("мы в функции process_task")
    try:
        process = Process.objects.get(id=process_id)
        print(f'----------------НАЧАЛО ГЕНЕРАЦИИ для процесса {process.id}----------------')

        source_img = [(f"{process.source_img.path}")]
        target_img = process.target_img.path
        output_img = process.output_img.path
        
        process.process_start_time = datetime.now()
        try:
            status = start(source_img=source_img, target_img=target_img, output_img=output_img, 
                upscale=process.inswapper_config_upscale, 
                codeformer_fidelity=process.inswapper_config_codeformer_fidelity)
        except Exception as e:
            print('\n\n\n\ОШИБКА В ЗАПУСКЕ start generation \n\n\n', e)
        process_take_time = datetime.now() - process.process_start_time

        print(f'-------------{output_img}--------------')

        print(f'-----------ИЗМЕНЕНИЕ В Process У ПРОЦЕССА {process.id}-------------')
        process.process_end_time = datetime.now()
        process.process_take_time = process_take_time
        process.process_ended = True
        process.save()

        print(f"ОТПРАВКА НА finish_task_status для процесса {process.id}")
        url = f"http://141.105.71.236:8585/finish_task_status"
        print(f'\n\n---- STATUS START {status}----\n\n')
        if status == False:
            data = {
                "task_status": 'ERROR_GENERATION',
                "id": process.task_id,
                # "user_id": process.for_user_id,
                # "emoji": process.emoji,
                # "original_photo_id": process.original_photo_id,

            }
            requests.post(url, data=data)

        else:
            with open(output_img, "rb") as f:
                # files = {"file": (f"image_{process.for_user_id}_{process.process_backend_id}.png", f)}
                files = {"file": (f"image_{process.id}.png", f)}
                data = {
                    "task_status": 'COMPLETED',
                    "id": process.task_id,
                    # "user_id": process.for_user_id,
                    # "emoji": process.emoji,
                    # "original_photo_id": process.original_photo_id,

                }
                requests.post(url, data=data, files=files)

        print(f'----------------ЗАВЕРШЕНИЕ ГЕНЕРАЦИИ для процесса {process.id}----------------')

    except Exception as e:
        print(f"Ошибка при обработке процесса {process_id}: {str(e)}")
        process = Process.objects.get(id=process_id)
        process.process_ended = True
        process.save()


def main():
    # Установите переменную окружения с настройками вашего проекта
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server_1.settings')
    # Настройка Django
    django.setup()
    from server_app.models import Process
    
    ctx = get_context('spawn')
    while True:
        try:
            unstarted_processes = Process.objects.filter(process_started=False)
            for process in unstarted_processes:
                process.process_started = True
                process.save()
                
                print("New proccess!!!")
                # Создаем новый процесс для каждой задачи
                process = ctx.Process(target=process_task, args=(process.id,))
                process.start()

        except Exception as e:
            print(f"Ошибка в главном цикле: {str(e)}")

        # print('Waiting...')
        time.sleep(1)


if __name__ == '__main__':
    main()
