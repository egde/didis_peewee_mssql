from peewee import Database, Context, ModelSelect
import pyodbc
import re
from loguru import logger

class MSSQLServer(Database):

    field_types = {
        'AUTO': 'INTEGER IDENTITY(1,1)',
        'INT GENERATED BY DEFAULT AS IDENTITY': 'INTEGER IDENTITY(1,1)',
        'BLOB': 'VARBINARY(MAX)'
        }
    
    def init(self, database, **kwargs) -> None:
        logger.info('''
            _    _            _        _____  _     _ _ _       _____                              __  __  _____ _____  ____  _      
            | |  | |          | |      |  __ \(_)   | (_| )     |  __ \                            |  \/  |/ ____/ ____|/ __ \| |     
            | |  | |_ __   ___| | ___  | |  | |_  __| |_|/ ___  | |__) |__  _____      _____  ___  | \  / | (___| (___ | |  | | |     
            | |  | | '_ \ / __| |/ _ \ | |  | | |/ _` | | / __| |  ___/ _ \/ _ \ \ /\ / / _ \/ _ \ | |\/| |\___ \\___ \| |  | | |     
            | |__| | | | | (__| |  __/ | |__| | | (_| | | \__ \ | |  |  __/  __/\ V  V /  __/  __/ | |  | |____) |___) | |__| | |____ 
            \____/|_| |_|\___|_|\___| |_____/|_|\__,_|_| |___/ |_|   \___|\___| \_/\_/ \___|\___| |_|  |_|_____/_____/ \___\_\______|
         
                    ''')
        return super().init(database, **kwargs)
    
    def _connect(self):
        driver = self.connect_params.get('driver') if self.connect_params.get('driver') is not None else '{ODBC Driver 18 for SQL Server}'
        server = self.connect_params.get('host')
        username = self.connect_params.get('user')
        password = self.connect_params.get('password')
        database = self.database
        trustserverauthentication = self.connect_params.get('trustservercertificate') if self.connect_params.get('trustservercertificate') is not None else 'no'
        authentication = self.connect_params.get('authentication') if self.connect_params.get('authentication') is not None else 'SqlPassword'
        connection_string = f'''
            Driver={driver};
            Server={server};
            Database={database};
            UID={username};
            PWD={password};
            trustservercertificate={trustserverauthentication};
            authentication={authentication}'''
        connection  = pyodbc.connect(connection_string, autocommit=True)
        return connection
    
    def get_tables(self, schema=None):
        if schema:
            query = '''
                SELECT 
                    TABLE_NAME 
                FROM 
                    INFORMATION_SCHEMA.TABLES 
                WHERE 
                    TABLE_SCHEMA = ? AND TABLE_TYPE = ? 
                ORDER BY 
                    TABLE_NAME'''
            cursor = self.execute_sql(sql=query, 
                                      params=(schema, 'BASE TABLE',))
        else:
            query = '''
                SELECT 
                    TABLE_NAME 
                FROM 
                    INFORMATION_SCHEMA.TABLES 
                WHERE
                     TABLE_TYPE = ? 
                ORDER BY 
                    TABLE_NAME'''

            cursor = self.execute_sql(sql=query, 
                                      params=('BASE TABLE',))

        return [r[0] for r in cursor.fetchall()]

    def last_insert_id(self, cursor, query_type = ...):
        return cursor.fetchone()[0]

    def _handle_create_table(self, query):
        if type(query) == Context:
            sql_elements: list[str] = query._sql

            if sql_elements[0] == 'CREATE TABLE ':
                if sql_elements[1] == 'IF NOT EXISTS ':
                    table_name = sql_elements[2].replace('"','')
                    adapted_sql = f'''IF OBJECT_ID(N'{table_name}', N'U') IS NULL '''
                    sql_elements = [adapted_sql] + sql_elements
                    sql_elements.remove('IF NOT EXISTS ')
                    query._sql = sql_elements
        return query

    def _handle_create_index(self, query):
        if type(query) == Context:
            sql_elements: list[str] = query._sql

            if sql_elements[0] == 'CREATE INDEX ' or sql_elements[0] == 'CREATE UNIQUE INDEX ':
                if sql_elements[1] == 'IF NOT EXISTS ':
                    index_name = sql_elements[2].replace('"','')
                    table_name = sql_elements[4].replace('"','')
                    adapted_sql = f'''IF NOT EXISTS (SELECT * FROM SYSINDEXES WHERE id=OBJECT_ID('{table_name}') and name='{index_name}') '''
                    sql_elements = [adapted_sql] + sql_elements
                    sql_elements.remove('IF NOT EXISTS ')
                    query._sql = sql_elements
        return query
    
    def _sql_select(self, sql:str, params:list):
        if sql.startswith('SELECT'):
            if 'LIMIT ? OFFSET ?' in sql:
                #  Get'LIMIT' and 'OFFSET' clauses to swap their values within the list of parameters
                parameters = re.findall(pattern=r'(\w*) \?', string=sql)
                for i in range(len(parameters)):
                    if parameters[i] == 'LIMIT':
                        ind_limit = i
                    if parameters[i] == 'OFFSET':
                        ind_offset = i
                limit = params[ind_limit]
                offset = params[ind_offset]
                params[ind_limit] = offset
                params[ind_offset] = limit
                
                # Adding ORDER 1 to order by the first column, if it is missing
                if not 'ORDER BY' in sql:
                    sql = sql.replace('LIMIT ? OFFSET ?', 'ORDER BY 1 OFFSET ? ROWS FETCH NEXT ? ROWS ONLY')
                else:
                    sql = sql.replace('LIMIT ? OFFSET ?', 'OFFSET ? ROWS FETCH NEXT ? ROWS ONLY')
            elif 'LIMIT ?' in sql:
                #  Get'LIMIT' and set it as the first parameter in TOP
                parameters = re.findall(pattern=r'(\w*) \?', string=sql)
                for i in range(len(parameters)):
                    if parameters[i] == 'LIMIT':
                        ind_limit = i
                limit = params.pop(ind_limit) # Remove parameters, TOP cannot be parameterized
                sql = sql.replace('SELECT', f'SELECT TOP {limit}') # use top
                sql = sql.replace('LIMIT ?', '') # Remove it
            elif 'OFFSET ?' in sql:
                sql = sql.replace('OFFSET ?', f'OFFSET ? ROWS') # use top
        return sql, params

            
    def _sql_insert(self, sql:str):
        if sql.startswith('INSERT INTO'):
            add = 'OUTPUT INSERTED.ID VALUES'
            sql = sql.replace('VALUES', add)
        return sql
        
    
    def execute(self, query, commit=..., **context_options):
        query = self._handle_create_table(query)
        query = self._handle_create_index(query)
        return super().execute(query, commit, **context_options)
    
    def execute_sql(self, sql, params = ..., commit=...):
        sql = self._sql_insert(sql)
        sql, params = self._sql_select(sql, params)
        logger.debug(f'''execute_sql - SQL: 
                            {sql}

                        Params: 
                            {params}''')
        return super().execute_sql(sql, params, commit)
    
    def get_binary_type(self):
        return bytes