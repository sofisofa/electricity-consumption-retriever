#!/usr/bin/env python3

import pytest
import psycopg2
from mockito import when, mock, verify, unstub
from src.electricity_consumption import init_database
import os
from dotenv import load_dotenv

DB_NAME = 'DB_NAME'
DB_USER = 'DB_USER'
DB_PW = 'DB_PW'
DB_PORT = 'DB_PORT'
DB_HOST = 'DB_HOST'

CONN_INFO = {
            "host": DB_HOST,
            "port": DB_PORT,
            "user": DB_USER,
            "password": DB_PW,
        }


class TestClassCreateDatabase:
    @pytest.fixture()
    def stub_connection(self):
        dummy_conn = mock()
        when(dummy_conn).close().thenReturn(None)
        when(dummy_conn).__enter__(...).thenReturn(dummy_conn)
        when(dummy_conn).__exit__(...).thenReturn(None)
        yield dummy_conn
        
    @pytest.fixture()
    def stub_cursor(self, stub_connection):
        dummy_conn = stub_connection
        dummy_cur = mock()
        when(dummy_conn).cursor().thenReturn(dummy_cur)
        when(dummy_cur).close().thenReturn(None)
        when(dummy_cur).__enter__(...).thenReturn(dummy_cur)
        when(dummy_cur).__exit__(...).thenReturn(None)
        yield dummy_cur

    @pytest.fixture()
    def stub_env_var(self, monkeypatch):
        monkeypatch.setenv('HOLALUZ_ENABLED', 'True')
        monkeypatch.setenv('ENDESA_ENABLED', 'True')
        yield
        
    @pytest.fixture()
    def init_var_for_table_creation(self):
        load_dotenv()
        hl_table_name = os.getenv('HL_TABLE_NAME')
        en_table_name = os.getenv('EN_TABLE_NAME')
        
        hl_create_table_q = f"CREATE TABLE IF NOT EXISTS {hl_table_name} (" \
                            "id BIGSERIAL PRIMARY KEY, " \
                            "date DATE, " \
                            "consumption FLOAT(8), " \
                            "cost FLOAT(8), " \
                            "creation_date TIMESTAMPTZ, " \
                            "modified_date  TIMESTAMPTZ);"

        en_create_table_q = f"CREATE TABLE IF NOT EXISTS {en_table_name} (" \
                            "id BIGSERIAL PRIMARY KEY, " \
                            "datetime TIMESTAMPTZ, " \
                            "consumption FLOAT(8), " \
                            "creation_date  TIMESTAMPTZ, " \
                            "modified_date  TIMESTAMPTZ);" \

        
        return [hl_create_table_q, en_create_table_q]
        
    @pytest.fixture(autouse=True)
    def unstub_after_test(self):
        yield
        unstub()
        
    def test_connected_to_database(self, stub_connection):
        dummy_conn = stub_connection
        when(psycopg2).connect(
            database=DB_NAME,
            host=CONN_INFO['host'],
            user=CONN_INFO['user'],
            password=CONN_INFO['password'],
            port=CONN_INFO['port'],
        ).thenReturn(dummy_conn)
        conn = init_database.connect_to_database(DB_NAME, CONN_INFO)
        assert conn == dummy_conn
    
    def test_not_connected_to_database(self):
        when(psycopg2).connect(
            host=CONN_INFO['host'],
            user=CONN_INFO['user'],
            password=CONN_INFO['password'],
            port=CONN_INFO['port'],
        ).thenRaise(Exception)
        
        with pytest.raises(Exception):
            init_database.connect_to_database(DB_NAME, CONN_INFO)

    def test_query_executed(self, stub_cursor, stub_connection):
        fake_query = 'This is a query'
        dummy_conn = stub_connection
        when(psycopg2).connect(
            database=DB_NAME,
            host=CONN_INFO['host'],
            user=CONN_INFO['user'],
            password=CONN_INFO['password'],
            port=CONN_INFO['port'],
        ).thenReturn(dummy_conn)
        dummy_cur = stub_cursor
        when(dummy_cur).execute(fake_query).thenReturn(None)
        when(dummy_cur).close().thenReturn(None)
        
        init_database.execute_query(fake_query, dummy_conn)
        
        verify(dummy_cur).execute(fake_query)
        
    def test_query_not_executed(self, stub_cursor, stub_connection):
        fake_query = 'This is a query'
        dummy_conn = stub_connection
        when(psycopg2).connect(
            database=DB_NAME,
            host=CONN_INFO['host'],
            user=CONN_INFO['user'],
            password=CONN_INFO['password'],
            port=CONN_INFO['port'],
        ).thenReturn(dummy_conn)
        dummy_cur = stub_cursor
        when(dummy_cur).execute(fake_query).thenRaise(Exception)
        
        with pytest.raises(Exception):
            init_database.execute_query(fake_query, dummy_conn)
    
    def test_run_connects_to_db_and_creates_the_tables(self, stub_env_var, stub_cursor, stub_connection, init_var_for_table_creation):
       
        hl_create_table_q = init_var_for_table_creation[0]
        
        en_create_table_q = init_var_for_table_creation[1]
        
        db_user = os.getenv('DB_USER')
        db_pw = os.getenv('DB_PASS')
        db_name = os.getenv('DB_NAME')
        db_port = os.getenv('DB_PORT')
        db_host = os.getenv('DB_HOST')
        dummy_conn = stub_connection
        
        when(psycopg2).connect(
            database=db_name,
            host=db_host,
            user=db_user,
            password=db_pw,
            port=db_port,
        ).thenReturn(dummy_conn)
        
        dummy_cur = stub_cursor
        when(dummy_cur).execute(en_create_table_q).thenReturn(None)
        when(dummy_cur).execute(hl_create_table_q).thenReturn(None)

        init_database.run()

        verify(dummy_cur).execute(en_create_table_q)
        verify(dummy_cur).execute(hl_create_table_q)

    def test_run_connects_to_db_and_hl_table_raises_exception(self, stub_env_var, stub_cursor, stub_connection, init_var_for_table_creation):
        hl_create_table_q = init_var_for_table_creation[0]
        
        en_create_table_q = init_var_for_table_creation[1]
        
        db_user = os.getenv('DB_USER')
        db_pw = os.getenv('DB_PASS')
        db_name = os.getenv('DB_NAME')
        db_port = os.getenv('DB_PORT')
        db_host = os.getenv('DB_HOST')
        
        dummy_conn = stub_connection
        when(psycopg2).connect(
            database=db_name,
            host=db_host,
            user=db_user,
            password=db_pw,
            port=db_port,
        ).thenReturn(dummy_conn)
    
        dummy_cur = stub_cursor
        when(dummy_cur).execute(en_create_table_q).thenReturn(None)
        when(dummy_cur).execute(hl_create_table_q).thenRaise(Exception("oh no!"))
    
        with pytest.raises(Exception):
            init_database.run()
    
    def test_run_connects_to_db_and_en_table_raises_exception(self, stub_env_var, stub_cursor, stub_connection, init_var_for_table_creation):
        hl_create_table_q = init_var_for_table_creation[0]
        
        en_create_table_q = init_var_for_table_creation[1]
        db_user = os.getenv('DB_USER')
        db_pw = os.getenv('DB_PASS')
        db_name = os.getenv('DB_NAME')
        db_port = os.getenv('DB_PORT')
        db_host = os.getenv('DB_HOST')
        
        dummy_conn = stub_connection
        when(psycopg2).connect(
            database=db_name,
            host=db_host,
            user=db_user,
            password=db_pw,
            port=db_port,
        ).thenReturn(dummy_conn)
        
        dummy_cur = stub_cursor
        when(dummy_cur).execute(hl_create_table_q).thenReturn(None)
        when(dummy_cur).execute(en_create_table_q).thenRaise(Exception("oh no!"))
        
        with pytest.raises(Exception):
            init_database.run()
        
        
if __name__ == "__main__":
    pytest.main([__file__])
