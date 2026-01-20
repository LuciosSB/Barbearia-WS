import os

OUTPUT_FILE = "codigo_consolidado.txt"

EXTENSOES_PERMITIDAS = {'.py', '.html', '.css', '.js', '.txt'}

ARQUIVOS_ESPECIFICOS = {'Procfile'}

PASTAS_IGNORADAS = {'venv', '.venv', '__pycache__', '.git', '.idea', 'uploads'}

def consolidar_projeto():
    diretorio_atual = os.getcwd()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
        for raiz, pastas, arquivos in os.walk(diretorio_atual):
            pastas[:] = [p for p in pastas if p not in PASTAS_IGNORADAS]
            for nome_arquivo in arquivos:
                caminho_completo = os.path.join(raiz, nome_arquivo)
                extensao = os.path.splitext(nome_arquivo)[1]
                if extensao in EXTENSOES_PERMITIDAS or nome_arquivo in ARQUIVOS_ESPECIFICOS:
                    if nome_arquivo == OUTPUT_FILE or nome_arquivo == "consolidar_projeto.py":
                        continue
                    relative_path = os.path.relpath(caminho_completo, diretorio_atual)
                    f_out.write(f"\n{'=' * 80}\n")
                    f_out.write(f"ARQUIVO: {relative_path}\n")
                    f_out.write(f"{'=' * 80}\n\n")
                    try:
                        with open(caminho_completo, "r", encoding="utf-8") as f_in:
                            f_out.write(f_in.read())
                    except Exception as e:
                        f_out.write(f"ERRO AO LER ARQUIVO: {e}")
                    f_out.write("\n\n")

    print(f"Sucesso! Todo o código foi consolidado em: {OUTPUT_FILE}")

if __name__ == "__main__":
    consolidar_projeto()