import os
import shutil
import glob

def delete_all_files():
        print("\n------------ Deletando arquivos do DOU")
        try:
            for folder in glob.glob('modulos/dou_api/dados/*'):
                #shutil.rmtree(folder)
                os.remove(folder)
                print("Arquivos deletados")
        except Exception as E: 
            print("Não foi possivel deletar os arquivos")
            print(E)

delete_all_files()
