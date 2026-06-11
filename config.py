import os


FOLDER_DB = "database"

if not os.path.exists(FOLDER_DB):
    os.makedirs(FOLDER_DB)


FILE_MEMORI = os.path.join(FOLDER_DB, "memori.json")
FILE_TASKS = os.path.join(FOLDER_DB, "tasks.json")
FILE_JADWAL = os.path.join(FOLDER_DB, "jadwal.json")
FILE_SESI_FOKUS = os.path.join(FOLDER_DB, "sesi_fokus.json")