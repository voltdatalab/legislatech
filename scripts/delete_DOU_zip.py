
import shutil
import glob

def delete_all_files():
        print("\n------------ Deletando arquivos do DOU")
        try:
            for folder in glob.glob('modulos/dou_api/dados/*'):
                shutil.rmtree(folder)
                print("Arquivos deletados")
        except: 
            print("Não foi possivel deletar os arquivos")

delete_all_files()