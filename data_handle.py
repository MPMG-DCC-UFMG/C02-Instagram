#!/usr/bin/python

import sys
import os
from datetime import datetime

import json

class DataHandle:
    """
    Contem metodos para persistir e recuperar dados, criar diretorios e formatar string de data-e-hora.
    Atributos
    ----------
    Metodos
    -------
    persistData(filename_output: str, document_list: list de str, operation_type: 'w' para write ou 'a' para append)
        Persite uma lista de documentos em um arquivo (filename_output) ou em outro meio apropriado.
    getData(filename_input: str, attributes_to_select: list de str)
        Retorna lista de documentos no arquivo (ou local) filename_input.
        Cada documento contem somente os atributos especificados em attributes_to_select
    create_directories(directories_list: list de str)
        Cria diretorios especificados em directories_list
    getDateFormatted(string_datetime: str, only_date: bool)
        Formata uma string de data e hora. Retorna data e hora ou somente a data de acordo com only_date
    """
    def __init__(self):
        self.profile_post_info_list = []
        self.post_info_list = []
        self.comment_info_list = []
        self.profile_comment_info_list = []

        self.unified_documents_list = []

        self.crawling_id = None

    def set_crawling_id(self, crawling_id):
        self.crawling_id = crawling_id


    ### TODO Adaptar KAFKA
    def persistData(self, filename_output, document_list, operation_type):
        ### GRAVA EM ARQUIVO
        ## self.__updateDataFile(filename_output=filename_output, document_list=document_list, operation_type=operation_type)
        ### Salva em memoria e grava no KAFKA
        if "profiles_posts.json" in filename_output:
            if operation_type == "w":
                self.profile_post_info_list = []
            self.profile_post_info_list.extend(document_list)
        elif "posts.json" in filename_output:
            if operation_type == "w":
                self.post_info_list = []
            self.post_info_list.extend(document_list)
        elif "profiles_comments.json" in filename_output:
            if operation_type == "w":
                self.profile_comment_info_list = []
            self.profile_comment_info_list.extend(document_list)
        elif "comments.json" in filename_output:
            if operation_type == "w":
                self.comment_info_list = []
            self.comment_info_list.extend(document_list)
        else:
            if operation_type == "w":
                self.unified_documents_list = []
            self.unified_documents_list.extend(document_list)


        #### (TODO) GRAVA no KAFKA --- usar o self.crawling_id


    def __updateDataFile(self,filename_output, document_list, operation_type):
        with open(filename_output, operation_type, encoding='utf-8') as file_output:
            for document in document_list:
                if document is not None:
                    json.dump(document, file_output)
                    file_output.write("\n")
                    file_output.flush()


    def getData(self, filename_input, attributes_to_select=None, document_type = None):
        ### Recupera de ARQUIVO
        ## return self.__getDataFromFile(filename_input=filename_input, attributes_to_select=attributes_to_select, document_type=document_type)
        ### Recupera de Memoria
        return self.__getDataFromMemory(filename_input=filename_input, attributes_to_select=attributes_to_select,
                                      document_type=document_type)

    def __getDataFromMemory(self, filename_input, document_type, attributes_to_select=None):
        document_list = []

        input_document_list = self.profile_post_info_list if "profiles_posts.json" in filename_input else (self.post_info_list if "posts.json" in filename_input else self.comment_info_list)

        for document_input in input_document_list:
            if document_type is None or (document_type is not None and document_input["tipo_documento"] == document_type):
                document_output = {}
                if attributes_to_select is not None and len(attributes_to_select) > 0:
                    for attribute_name in attributes_to_select:
                        document_output[attribute_name] = document_input[attribute_name]
                else:
                    document_output = document_input

                document_list.append(document_output)

        return(document_list)



    def __getDataFromFile(self, filename_input, attributes_to_select=None, document_type=None):
        document_list = []

        if (os.path.exists(filename_input) is True):
            with open(filename_input, "r", encoding='utf-8') as file_input:
                for document in file_input:
                    document_input = json.loads(document)

                    if document_type is None or (document_type is not None and document_input["tipo_documento"] == document_type):
                        document_output = {}
                        if attributes_to_select is not None and len(attributes_to_select) > 0:
                            for attribute_name in attributes_to_select:
                                document_output[attribute_name] = document_input[attribute_name]
                        else:
                            document_output = document_input

                        document_list.append(document_output)

        return(document_list)

    def create_directories(self,directories_list):
        for directory in directories_list:
            # print("Creating directory", directory, flush=True)
            try:
                os.mkdir(directory)
            except FileExistsError:
                pass

    def getDateFormatted(self, string_datetime, only_date=False):
        a_datetime = None
        string_datetime = string_datetime.replace("\"", "")
        string_datetime = string_datetime.replace("'", "")
        if only_date is True:
            try:
                a_datetime = datetime.strptime(string_datetime, '%Y-%m-%d')
            except Exception as e:
                try:
                    a_datetime = datetime.strptime(string_datetime, '%d-%m-%Y')
                except Exception as e:
                    print("Erro ao formatar data do tipo:", string_datetime, "Erro detalhado:", e, flush=True)
        else:
            try:
                a_datetime = datetime.strptime(string_datetime, '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                try:
                    a_datetime = datetime.strptime(string_datetime, '%Y-%m-%d %H:%M:%S.%f')
                except Exception as e:
                    try:
                        a_datetime = datetime.strptime(string_datetime, '%Y-%m-%dT%H:%M:%SZ')
                    except Exception as e:
                        try:
                            a_datetime = datetime.strptime(string_datetime, '%a %b %d %H:%M:%S +0000 %Y')
                        except Exception as e:
                            try:
                                a_datetime = datetime.strptime(string_datetime, '%d-%m-%Y %H:%M:%S')
                            except Exception as e:
                                print("Erro ao formatar data do tipo:", string_datetime,
                                      "\tNao foi possivel identificar um padrao na string.", flush=True)
        return (a_datetime)

