#!/usr/bin/python

import sys
import os
from datetime import datetime

from data_handle import DataHandle
import local_instaloader.instaloader as localinstaloader
from data_collection import DataCollection

import json


TARGET_JSON_FOLDER = "/var/instagram-crawler/jsons/"
INPUT_JSON_FOLDER = "/var/instagram-crawler/"

# TARGET_JSON_FOLDER = "/data/jsons/"
# INPUT_JSON_FOLDER = "/data/"

DEFAULT_MAX_COMMENTS = 5000
DEFAULT_MAX_POSTS = 5000

try:
    os.makedirs(TARGET_JSON_FOLDER)
except Exception as e:
    pass

class Coletor():
    """
    Recebe os parametros de entrada, gerencia os proxies e organiza a chamada das coletas.
    Atributos
    ----------
    data_path: str
        Pasta onde os dados da coleta serao persistidos
    instagram_user: str
        Usuario do Instagram para fazer login
    instagram_passwd: str
        Senha de usuario do Instagram para fazer login
    proxy_list: list de str
        Lista de proxies
    collection_type: str
        Se a coleta e de 'usuarios' ou 'hashtags'
    user_list : list de str
        Lista de usuarios a serem monitoradas
    hashtag_list : list de str
        Lista de palavras-chave (hashtags)
    min_date : objeto datetime
        Data limite inferior da coleta.
    max_date : objeto datetime
        Data limite superior da coleta.
    max_posts: int
        Numero maximo de posts a serem coletados no periodo
    max_comments: int
        Numero maximo de comentarios por posts a serem coletados
    Metodos
    -------
    Construtor(Json)
        Construtor da classe. Recebe uma string de json com as informacoes necessarias para a coleta.
    create_collection_pipeline()
        Inicializa o processo de coleta de acordo com os parametros de entrada.
    """
    def __init__(self, input_json):
        try:
            self.data_path = TARGET_JSON_FOLDER

            self.instagram_user = input_json['login_usuario']
            self.instagram_passwd = input_json['login_senha']

            self.proxy_list = input_json['lista_de_proxies']

            self.user_list = input_json['usuarios']
            self.hashtag_list = []

            for hashtag in input_json['palavras']:
                self.hashtag_list.append(str(hashtag).replace("#", ""))

            self.users_to_download_media = input_json['usuarios_a_baixar_midias']

            self.hashtags_to_download_media = []
            for hashtag in input_json['palavras_a_baixar_midias']:
                self.hashtags_to_download_media.append(str(hashtag).replace("#", ""))

            dataHandle = DataHandle()
            self.min_date = dataHandle.getDateFormatted(str(input_json['data_min']), only_date=True) if input_json['data_min'] is not None else None
            self.max_date = dataHandle.getDateFormatted(str(input_json['data_max']), only_date=True) if input_json['data_max'] is not None else None

            self.max_posts = input_json['maximo_posts'] if input_json['maximo_posts'] is not None else DEFAULT_MAX_POSTS
            self.max_comments = input_json['maximo_comentarios'] if input_json['maximo_comentarios'] is not None else DEFAULT_MAX_COMMENTS

            self.proxy_index = 0
            self.max_attempts = len(self.proxy_list)+1

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('\nErro: ', e, '\tDetalhes: ', exc_type, fname, exc_tb.tb_lineno, '\tData e hora: ', datetime.now(),
                  flush=True)

            print("Finalizando script...")
            sys.exit(1)


        '''
        Cria pasta de saida
        '''
        self.__create_data_path()

    def __create_data_path(self):
        dataHandle = DataHandle()

        self.current_timestamp = str(datetime.now().timestamp()).replace(".", "_")


        directory_list = ['{}{}/'.format(self.data_path , self.current_timestamp),
                                   '{}{}/{}/'.format(self.data_path , self.current_timestamp, "medias")]

        dataHandle.create_directories(directories_list=directory_list)

        self.data_path_source_files = '{}{}/'.format(self.data_path , self.current_timestamp)

        self.filename_posts = '{}{}/{}'.format(self.data_path , self.current_timestamp,"posts.json")
        self.filename_comments = '{}{}/{}'.format(self.data_path, self.current_timestamp, "comments.json")
        self.filename_profiles_posts = '{}{}/{}'.format(self.data_path, self.current_timestamp, "profiles_posts.json")
        self.filename_profiles_comments = '{}{}/{}'.format(self.data_path, self.current_timestamp, "profiles_comments.json")
        self.filepath_medias ='{}{}/{}/'.format(self.data_path , self.current_timestamp, "medias")

        self.filename_unified_data_file = '{}{}/{}'.format(self.data_path , self.current_timestamp,str(self.current_timestamp)+".json")


    def __get_proxy(self, does_not_increment=False):
        proxies = None

        try:
            if len(self.proxy_list) > 0:
                self.proxy_index = 0 if self.proxy_index >= len(self.proxy_list) else self.proxy_index
                proxy = self.proxy_list[self.proxy_index]

                if does_not_increment is False:
                    self.proxy_index += 1

                proxies = {
                    'http': "http://"+proxy,
                    'https': "https://"+proxy
                }

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('\nErro: ', e, '\tDetalhes: ', exc_type, fname, exc_tb.tb_lineno, '\tData e hora: ', datetime.now(),
                  flush=True)

            print("Finalizando script...")
            sys.exit(1)
        finally:
            return proxies


    def __getErrorDocument(self, exception_obj, exc_type, exc_tb):
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        error_str = '{}'.format(str(exception_obj))
        error_details = '{} {} {}'.format(exc_type, fname, exc_tb.tb_lineno)

        error_document = {"erro": error_str, "detalhes": error_details, "data_e_hora": str(datetime.now())}

        return error_document

    def __create_unified_data_file(self, filename_output):
        try:
            total_lines = 0
            input_filename_list = [self.filename_posts, self.filename_comments, self.filename_profiles_posts,
                                   self.filename_profiles_comments]

            dataHandle = DataHandle()
            for filename_input in input_filename_list:
                document_input_list = dataHandle.getData(filename_input=filename_input)
                total_lines += len(document_input_list)
                dataHandle.persistData(filename_output=filename_output, document_list=document_input_list, operation_type="a")


            ### Cria documento para indicar local das midias
            if total_lines > 0:
                alias_filepath_medias = '{}{}/{}/'.format("/data/jsons/", self.current_timestamp, "medias")
                document_input_list = [{"tipo_documento":"midia", "local_armazenamento": alias_filepath_medias}]
                dataHandle.persistData(filename_output=filename_output, document_list=document_input_list,
                                       operation_type="a")


        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('\nErro: ', e, '\tDetalhes: ', exc_type, fname, exc_tb.tb_lineno, '\tData e hora: ', datetime.now(),
                  flush=True)

            print("Finalizando script...")
            sys.exit(1)

    def __create_error_file(self, filename_output, error_document):
        try:
            dataHandle = DataHandle()
            dataHandle.persistData(filename_output=filename_output, document_list=[error_document],
                                       operation_type="w")
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('\nErro: ', e, '\tDetalhes: ', exc_type, fname, exc_tb.tb_lineno, '\tData e hora: ', datetime.now(),
                  flush=True)

            print("Finalizando script...")
            sys.exit(1)

    def __execute_data_collection(self, filename_output, dataHandle, document_input_list, debug_message, document_type):
        collection_sucess = False
        error_document = None
        has_error = False

        try:
            collection_attempts = 0

            while collection_sucess is False and collection_attempts < self.max_attempts:
                prefix_str = "(Re)" if collection_attempts > 0 else " "
                a_message = "{}{}".format(prefix_str, debug_message)
                print("\n")
                print(a_message, '\tData e hora: ', datetime.now(),flush=True)

                proxy_info = self.__get_proxy()
                instaloaderInstance = localinstaloader.Instaloader(proxies=proxy_info)

                if document_type == "posts_hashtag":
                    instaloaderInstance.login(user=self.instagram_user, passwd=self.instagram_passwd)

                dataCollection = DataCollection(filename_output=filename_output, dataHandle=dataHandle,
                                                instaloaderInstance=instaloaderInstance,
                                                instaloaderClass=localinstaloader,
                                                document_type=document_type)

                if proxy_info is None:
                    print("\t!!!ATENCAO!!!: Esta coleta nao esta utilizando proxy.")
                else:
                    proxy_alias = proxy_info["https"].split("@")[1]
                    print("\tUtilizando o proxy:", proxy_alias)

                documents_collected = 0
                for document_input in document_input_list:
                    documents_collected +=1
                    if document_type == "profiles_posts":
                        print("\tColetando perfil do usuario {}".format(document_input), '\tData e hora: ', datetime.now(),
                              flush=True)
                        has_error, error_document = dataCollection.collectProfile(username=document_input)
                    elif document_type == "posts_profile":
                        print("\tColetando posts do usuario {} {}/{}".format(document_input["nome_do_usuario"], documents_collected, len(document_input_list)),
                              '\tData e hora: ',
                              datetime.now(), "\n",
                              flush=True)
                        has_error, error_document = dataCollection.collectPosts(data_min=self.min_date,
                                                                                 data_max=self.max_date,
                                                                                 post_limit=self.max_posts,
                                                                                 username=document_input['nome_do_usuario'],
                                                                                 hashtag=None)
                    elif document_type == "posts_hashtag":
                        print("\tColetando posts da hashtag {}".format(document_input),
                              '\tData e hora: ', datetime.now(), "\n",
                              flush=True)
                        has_error, error_document = dataCollection.collectPosts(data_min=self.min_date,
                                                                                 data_max=self.max_date,
                                                                                 post_limit=self.max_posts,
                                                                                 username=None, hashtag=document_input)
                    elif document_type == "media":
                        print("\tColetando media do post {} {}/{}".format(document_input['identificador'], documents_collected, len(document_input_list)),'\tData e hora: ', datetime.now(), flush=True)
                        has_error, error_document = dataCollection.downloadPostMedia(
                            post_id=document_input['identificador'],
                            media_url=document_input['identificador_midia'])
                    elif document_type == "comments_profile" or document_type == "comments_hashtag":
                        print("\tColetando comments do post {} {}/{}".format(document_input['identificador'],documents_collected,len(document_input_list)),'\tData e hora: ', datetime.now(),flush=True)
                        has_error, error_document = dataCollection.collectComments(
                            post_id=document_input['identificador'],
                            comments_by_post_limit=self.max_comments,
                            line_debug_number=1000)
                    elif document_type == "profiles_comments":
                        print("\tColetando perfil do usuario {} {}/{}".format(document_input['nome_do_usuario'], documents_collected, len(document_input_list)), '\tData e hora: ', datetime.now(),
                              flush=True)
                        has_error, error_document = dataCollection.collectProfile(username=document_input['nome_do_usuario'])
                    else:
                        print("Tipo de coleta nao identificado. Finalizando script...")
                        sys.exit(1)

                    if has_error is True:
                        if "429" in error_document:
                            print("Muitas requisicoes feitas recentemente. Erro:", error_document)
                        collection_attempts += 1
                        collection_sucess = False
                        break
                    else:
                        collection_sucess = True

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("\nProcesso de coleta sera finalizado devido a erro. O erro: ", e, '\tDetalhes: ', exc_type, fname, exc_tb.tb_lineno, '\tData e hora: ',datetime.now(),flush=True)

            exc_type, exc_obj, exc_tb = sys.exc_info()
            error_document = self.__getErrorDocument(exception_obj=e, exc_type=exc_type, exc_tb=exc_tb)

            self.__create_error_file(filename_output=self.filename_unified_data_file,
                                     error_document=error_document)
            print("Finalizando script.")
            sys.exit(1)
        finally:
            if has_error is True:
                print("{}{}".format("\nProcesso de coleta sera finalizado devido a erro. O erro: ",
                                    error_document), flush=True)
                self.__create_error_file(filename_output=self.filename_unified_data_file,
                                         error_document=error_document)
                sys.exit(1)


    def create_collection_pipeline(self):
        try:
            start_time = str(datetime.now())
            dataHandle = DataHandle()

            start_time = str(dataHandle.getDateFormatted(string_datetime=start_time))

            # print("Processo de coleta iniciado em {}\tSalvando dados em {}".format(start_time, self.data_path_source_files), flush=True)

            self.alias_data_path_source_files = '{}{}/'.format("/data/jsons/", self.current_timestamp)
            print("Processo de coleta iniciado em {}\tSalvando dados em {}".format(start_time,self.alias_data_path_source_files),
                  flush=True)

            collection_types = []

            if len(self.user_list) > 0:
                collection_types.append("perfil")
            if len(self.hashtag_list) > 0:
                collection_types.append("hashtag")


            if len(collection_types) == 0:
                print("\nNenhum perfil ou hashtag informado para coleta. Finalizando script ", flush=True)
                self.__create_error_file(filename_output=self.filename_unified_data_file,
                                         error_document={"erro": "Nenhum perfil ou hashtag informado para coleta.",
                                                         "detalhes": None,
                                                         "data_e_hora": str(datetime.now())})
                sys.exit(1)


            for collection_type in collection_types:

                post_type_to_download_midias_and_comments = None

                if collection_type == "perfil":
                    ### COLETA 1.1 - PERFIL
                    document_input_list=self.user_list
                    filename_output = self.filename_profiles_posts

                    self.__execute_data_collection(filename_output=filename_output, dataHandle=dataHandle,
                                                   document_input_list=document_input_list,
                                                   debug_message="Inicio da coleta de perfil de usuarios",
                                                   document_type="profiles_posts")

                    ### COLETA 1.2 - POSTS DE PERFIL
                    document_input_list = dataHandle.getData(filename_input=self.filename_profiles_posts, attributes_to_select=['nome_do_usuario'])
                    filename_output = self.filename_posts

                    if len(document_input_list) > 0:
                        post_type_to_download_midias_and_comments = "posts_profile"

                        self.__execute_data_collection(filename_output=filename_output, dataHandle=dataHandle,
                                                       document_input_list=document_input_list,
                                                       debug_message="Inicio da coleta de posts de usuario",
                                                       document_type=post_type_to_download_midias_and_comments)

                    else:
                        print("\nAtencao: Nao existem perfis armazenados para coletar posts.",flush=True)

                if collection_type == "hashtag":
                    ### COLETA 1 -POSTS DE HASHTAGS

                    ### Verifica se login valido
                    try:
                        proxy_info = self.__get_proxy(does_not_increment=True)
                        instaloaderInstance = localinstaloader.Instaloader(proxies=proxy_info)
                        instaloaderInstance.login(user=self.instagram_user, passwd=self.instagram_passwd)
                    except Exception as e:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        print('\nErro: ', e, '\tDetalhes: ', exc_type, fname, exc_tb.tb_lineno, '\tData e hora: ',
                              datetime.now(),
                              flush=True)

                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        error_document = self.__getErrorDocument(exception_obj=e, exc_type=exc_type, exc_tb=exc_tb)

                        self.__create_error_file(filename_output=self.filename_unified_data_file,
                                                 error_document=error_document)
                        print("Finalizando script.")
                        sys.exit(1)
                    else:
                        document_input_list = self.hashtag_list
                        filename_output = self.filename_posts

                        post_type_to_download_midias_and_comments = "posts_hashtag"

                        self.__execute_data_collection(filename_output=filename_output, dataHandle=dataHandle,
                                                       document_input_list=document_input_list,
                                                       debug_message="Inicio da coleta de posts com hashtag",
                                                       document_type=post_type_to_download_midias_and_comments)


                ### COLETA 2 - MIDIA DOS POSTS
                filepath_output = self.filepath_medias
                post_document_input_list = []

                temp_post_document_input_list = dataHandle.getData(filename_input=self.filename_posts,
                                                         attributes_to_select=['identificador', "identificador_midia",
                                                                               "tipo_midia", "identificador_coleta"],
                                                         document_type=post_type_to_download_midias_and_comments)

                identifiers_to_download_midia = self.users_to_download_media if collection_type == "perfil" else self.hashtags_to_download_media

                ### Faz a verificacao de quais perfis ou palavras para coletar midias
                if len(identifiers_to_download_midia) > 0:
                    for temp_document in temp_post_document_input_list:
                        if temp_document["identificador_coleta"] in identifiers_to_download_midia:
                            post_document_input_list.append(temp_document)
                else:
                    post_document_input_list = temp_post_document_input_list

                if len(post_document_input_list) > 0:
                    self.__execute_data_collection(filename_output=filepath_output, dataHandle=dataHandle,
                                                   document_input_list=post_document_input_list,
                                                   debug_message="Inicio da coleta de media dos posts",
                                                   document_type="media")
                else:
                    print("\nAtencao: Nao existem posts armazenados para coletar midia.", flush=True)

                ### COLETA 3 - COMENTARIOS DOS POSTS
                document_input_list = dataHandle.getData(filename_input=self.filename_posts,
                                                         attributes_to_select=['identificador'],
                                                         document_type=post_type_to_download_midias_and_comments)
                filename_output = self.filename_comments
                comment_type_to_download_profiles = "comments_profile" if post_type_to_download_midias_and_comments == "posts_profile" else "comments_hashtag"

                if len(document_input_list) > 0:
                    self.__execute_data_collection(filename_output=filename_output, dataHandle=dataHandle,
                                                   document_input_list=document_input_list,
                                                   debug_message="Inicio da coleta de comments dos posts",
                                                   document_type=comment_type_to_download_profiles)
                else:
                    print("\nAtencao: Nao existem posts armazenados para coletar comentarios.", flush=True)

                ### COLETA 4 - PERFIL DOS COMENTADORES
                document_input_list = dataHandle.getData(filename_input=self.filename_comments,
                                                         attributes_to_select=['nome_do_usuario'],
                                                         document_type=comment_type_to_download_profiles)
                filename_output = self.filename_profiles_comments

                if len(document_input_list) > 0:
                    self.__execute_data_collection(filename_output=filename_output, dataHandle=dataHandle,
                                                   document_input_list=document_input_list,
                                                   debug_message="Inicio da coleta de perfil de comentadores",
                                                   document_type="profiles_comments")
                else:
                    print("\nAtencao: Nao existem comentarios armazenados para coletar perfis de comentadores.", flush=True)


            self.__create_unified_data_file(filename_output=self.filename_unified_data_file)



        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('\nErro: ', e, '\tDetalhes: ', exc_type, fname, exc_tb.tb_lineno, '\tData e hora: ', datetime.now(),
                  flush=True)

            exc_type, exc_obj, exc_tb = sys.exc_info()
            error_document = self.__getErrorDocument(exception_obj=e, exc_type=exc_type, exc_tb=exc_tb)

            self.__create_error_file(filename_output=self.filename_unified_data_file,
                                     error_document=error_document)
            print("Finalizando script.")
            sys.exit(1)



def main():
    try:
        start_time = datetime.now()

        '''
        --------------------------------------------------------
        Le dados de entrada
        '''
        try:
            cmd = sys.argv[1]
        except:
            print("Erro: Nenhuma entrada informada. Fechando script...")
            sys.exit(1)

        try:
            if cmd == "-d":
                json_dump_input = sys.argv[2]
                json_dump_input = json_dump_input.replace("'", '"')
                input_json = json.loads(json_dump_input)
            else:
                filename_data_input = str(INPUT_JSON_FOLDER +sys.argv[1])

                with open(filename_data_input, "r", encoding="utf-8") as file_input:
                    input_json = json.load(file_input)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('\nErro na entrada de dados: ', e, '\tDetalhes: ', exc_type, fname, exc_tb.tb_lineno, '\tFechando script: ',flush=True)
            sys.exit(1)

        '''
        --------------------------------------------------------
        Testa se dados de entrada sao validos
        '''
        attributes_to_run = ['lista_de_proxies',
                             "login_usuario","login_senha",
                             'usuarios',"usuarios_a_baixar_midias",
                             'palavras', "palavras_a_baixar_midias",
                             'data_min','data_max',
                             'maximo_posts','maximo_comentarios',
                             "pasta_da_saida", "coletor"]


        attributes_not_provided = [x for x in attributes_to_run if x not in input_json]

        if len(attributes_not_provided) > 0:
            error_msg = "Erro: O atributo: {} não foi informado " if len(attributes_not_provided) == 1 else  "Erro: Os atributos: {} não foram informados "

            print(str(error_msg+"na entrada. Fechando script...").format(", ".join(attributes_not_provided)))
            sys.exit(1)
        '''

        --------------------------------------------------------
        Inicia coleta
        '''

        c = Coletor(input_json=input_json)
        c.create_collection_pipeline()

        end_time = datetime.now()
        print("\nData de inicio: %s\nData final: %s\nTempo de execucao (minutos): %s\n" % (start_time, end_time, ((end_time - start_time).seconds)/60))

        print("\n\n###########################################################\tSCRIPT FINALIZADO.", flush=True)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print('\nErro: ', e, '\tDetalhes: ', exc_type, fname, exc_tb.tb_lineno, '\tData e hora: ', datetime.now(),
              flush=True)

if __name__ == '__main__':
    main()

