# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
DOTENV_PATH = os.path.join(BASE_PATH, '.env')
load_dotenv(DOTENV_PATH)

import logging
import pyodbc
from pysendpulse.pysendpulse import PySendPulse
from datetime import datetime

### logger
logger = logging.getLogger(__name__)
logger_handler = logging.FileHandler(os.path.join(BASE_PATH, '{}.log'.format(__file__)))
logger_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
logger_handler.setFormatter(logger_formatter)
logger.addHandler(logger_handler)
logger.setLevel(logging.WARNING)
logger.propagate = False

# logger.error('We have a problem')
# logger.info('While this is just chatty')

def main():

    SENDPULSE_REST_API_ID = os.getenv('SENDPULSE_REST_API_ID', '')
    SENDPULSE_REST_API_SECRET = os.getenv('SENDPULSE_REST_API_SECRET', '')
    SENDPULSE_TOKEN_STORAGE = os.getenv('SENDPULSE_TOKEN_STORAGE', 'memcached')
    SENDPULSE_CLIENT_INFO_ID = os.getenv('SENDPULSE_CLIENT_INFO_ID', '')

    MSSQL_DRIVER = os.getenv('MSSQL_DRIVER', '{FreeTDS}')
    MSSQL_TDS_VERSION = os.getenv('MSSQL_TDS_VERSION', 8.0)
    MSSQL_SERVER = os.getenv('MSSQL_SERVER')
    MSSQL_PORT = os.getenv('MSSQL_PORT', 1433)
    MSSQL_DATABASE = os.getenv('MSSQL_DATABASE')
    MSSQL_UID = os.getenv('MSSQL_UID')
    MSSQL_PWD = os.getenv('MSSQL_PWD')

    MSSQL_CONNECTION_STRING = 'DRIVER={DRIVER};' \
        'SERVER={SERVER};' \
        'PORT={PORT};' \
        'DATABASE={DATABASE};' \
        'UID={UID};' \
        'PWD={PWD};' \
        'TDS_Version={TDS_VERSION};'.format(
        DRIVER=MSSQL_DRIVER,
        TDS_VERSION=MSSQL_TDS_VERSION,
        SERVER=MSSQL_SERVER,
        PORT=MSSQL_PORT,
        DATABASE=MSSQL_DATABASE,
        UID=MSSQL_UID,
        PWD=MSSQL_PWD,
    )

    MSSQL_DATABASE_CONNECTION = pyodbc.connect(MSSQL_CONNECTION_STRING)
    # MSSQL_DATABASE_CONNECTION.setencoding('utf-8')

    MSSQL_DATABASE_CURSOR = MSSQL_DATABASE_CONNECTION.cursor()

    try:
        SPApiProxy = PySendPulse(SENDPULSE_REST_API_ID, SENDPULSE_REST_API_SECRET, SENDPULSE_TOKEN_STORAGE)

        with MSSQL_DATABASE_CONNECTION:
            MSSQL_DATABASE_CURSOR.execute("\
                SELECT DISTINCT [Номер анкеты] AS form_id \
                    ,[Дата создания] AS created_at \
                    ,[Фамилия] AS surname \
                    ,[Имя] AS first_name \
                    ,[Отчество] AS second_name \
                    ,[Дата рождения] AS birth_date \
                    ,[Пол.Название] AS sex \
                    ,[Электронная почта] AS email \
                    ,[Основной телефон.Номер] AS phone \
                    ,[Первый звонок] AS first_call \
                    ,[Последний звонок] AS last_call \
                    ,[Первая встреча] AS first_meeting \
                    ,[Последняя встреча] AS last_meeting \
                    ,[TS] AS ts \
                FROM [a2profile_fh].[dbo].[tGetClientInfo] \
                WHERE [Электронная почта] IS NOT NULL AND [Электронная почта] != ''"
            )

            emails_for_add = []

            for row in MSSQL_DATABASE_CURSOR.fetchall():
                form_id = row[0] or ''
                if row[1]:
                    created_at = row[1].strftime('%Y-%m-%d')
                else:
                    created_at = ''

                if row[2]:
                    surname = row[2].split('-')[0].capitalize() or ''
                else:
                    surname = ''

                if row[3]:
                    first_name = row[3].split('-')[0].capitalize() or ''
                else:
                    first_name = ''

                if row[4]:
                    second_name = row[4].split('-')[0].capitalize() or ''
                else:
                    second_name = ''

                if row[5]:
                    birth_date = row[5].strftime('%Y-%m-%d')
                else:
                    birth_date = ''

                sex = row[6] or ''
                email = row[7] or ''
                phone = row[8] or ''

                if row[9]:
                    first_call = row[9].strftime('%Y-%m-%d')
                else:
                    first_call = ''

                if row[10]:
                    last_call = row[10].strftime('%Y-%m-%d')
                else:
                    last_call = ''

                if row[11]:
                    first_meeting = row[11].strftime('%Y-%m-%d')
                else:
                    first_meeting = ''

                if row[12]:
                    last_meeting = row[12].strftime('%Y-%m-%d')
                else:
                    last_meeting = ''

                ts = row[13] or ''

                if email:
                    emails_for_add.append({
                        'email': email,
                        'variables': {
                            'phone': phone,
                            # 'form_id': form_id,
                            'created_at': created_at,
                            # 'surname': surname,
                            'first_name': first_name,
                            # 'second_name': second_name,
                            'birth_date': birth_date,
                            'sex': sex,
                            'first_call': first_call,
                            'last_call': last_call,
                            # 'first_meeting': first_meeting,
                            # 'last_meeting': last_meeting,
                        }
                    })

            SPApiProxy.add_emails_to_addressbook(SENDPULSE_CLIENT_INFO_ID, emails_for_add)
    except Exception as e:
        logger.exception(str(e))

if __name__ == '__main__':
    main()
