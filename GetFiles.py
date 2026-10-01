import cgi
import os

params = cgi.FieldStorage()
print('Content-type: text/html\n')

a = str(params.getfirst('a', ''))

if a == '':
    # Если параметр 'a' не указан, отправляем ошибку
    print("Error: No file parameter specified")
elif a=="GetErrors":
    try:
        # Проверяем существование файла
        a = "errors.txt"
        if not os.path.exists(a):
            raise FileNotFoundError(f"File {a} not found")

        # Получаем размер файла
        file_size = os.path.getsize(a)

        # Отправляем заголовки для скачивания
        print(f"Content-Disposition: attachment; filename=\"{os.path.basename(a)}\"")
        print(f"Content-Length: {file_size}")
        print("Content-Type: application/octet-stream\n")

        # Читаем и отправляем файл
        with open(a, "rb") as file:
            print(file.read().decode('latin-1'))
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")
elif a=="GetDB":
    try:
        a = 'sait.db'
        # Проверяем существование файла
        if not os.path.exists(a):
            raise FileNotFoundError(f"File {a} not found")

        # Получаем размер файла
        file_size = os.path.getsize(a)

        # Отправляем заголовки для скачивания
        print(f"Content-Disposition: attachment; filename=\"{os.path.basename(a)}\"")
        print(f"Content-Length: {file_size}")
        print("Content-Type: application/octet-stream\n")

        # Читаем и отправляем файл
        with open(a, "rb") as file:
            print(file.read().decode('latin-1'))
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")