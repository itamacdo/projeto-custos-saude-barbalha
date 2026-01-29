import pandas as pd
import requests
import io
import os

def coletar_dados_saude():
    if not os.path.exists('data'):
        os.makedirs('data')

    # URL de Unidades de Saúde (Dados Abertos)
    url = "https://pms-dados-abertos.s3.sa-east-1.amazonaws.com/dados_abertos/unidades_saude.csv"
    
    print("Tentando conectar ao servidor de dados...")
    
    # Cabeçalho para fingir que somos um navegador Chrome
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # Baixando os dados com verificação de SSL desligada se necessário
        response = requests.get(url, headers=headers, verify=False)
        
        if response.status_code == 200:
            # Lendo o conteúdo baixado
            content = response.content.decode('utf-8')
            df = pd.read_csv(io.StringIO(content), sep=';')
            
            # Salvando o CSV limpo
            df.to_csv('data/unidades_saude.csv', index=False)
            print("✅ Sucesso! O arquivo 'data/unidades_saude.csv' foi criado.")
        else:
            print(f"❌ O servidor negou o acesso. Código: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    coletar_dados_saude()