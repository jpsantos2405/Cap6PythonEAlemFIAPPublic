import os
import json
import oracledb
import pandas as pd
import configparser
from datetime import datetime

# ---------------- CONFIG ----------------
config = configparser.ConfigParser()
config.read('config.ini')

db_user = config.get('database', 'user')
db_password = config.get('database', 'password')
db_dsn = config.get('database', 'dsn')

try:
    conn = oracledb.connect(user=db_user, password=db_password, dsn=db_dsn)
    c = conn.cursor()
except Exception as e:
    print("Erro:", e)
    exit()

m = ' ' * 4

# ---------------- FUNÇÕES GENÉRICAS ----------------

def insert(sql, params):
    c.execute(sql, params)
    conn.commit()

def update(sql, params):
    c.execute(sql, params)
    conn.commit()

def delete(sql, params):
    c.execute(sql, params)
    conn.commit()

def select(sql, params=[]):
    c.execute(sql, params)
    return c.fetchall()

def validar_data(data):
    try:
        datetime.strptime(data, "%d/%m/%Y")
        return True
    except:
        return False

def get_id_animal(ident):
    r = select("SELECT idAnimal FROM animal WHERE identificadorAnimal=:1", [ident])
    return r[0][0] if r else None

def atualizar_atrasados():
    update("""
        UPDATE agendamento
        SET statusAgendamento = 'atrasado'
        WHERE statusAgendamento = 'agendado'
        AND dataAgendamento < SYSDATE
    """, [])

def animal_esta_vivo(idAnimal):
    r = select("""
        SELECT dataFalecimentoAnimal
        FROM animal
        WHERE idAnimal = :1
    """, [idAnimal])

    if not r:
        return False

    return r[0][0] is None

def pedir_periodo():
    data_ini = input("Data inicial (DD/MM/YYYY): ")
    data_fim = input("Data final (DD/MM/YYYY): ")

    if not validar_data(data_ini) or not validar_data(data_fim):
        print("Data inválida")
        input()
        return None, None

    return data_ini, data_fim

def data_no_passado(data_str):
    data = datetime.strptime(data_str, "%d/%m/%Y")
    return data.date() < datetime.now().date()

# ---------------- MENUS ----------------

def menu_principal():
    print("==== SISTEMA FAZENDA ====")
    print("""
    1 - Animais
    2 - Vacinas
    3 - Agendamentos
    4 - Relatórios
    5 - Sair
    """)
    return input(m + "Escolha -> ")

def menu_secundario(titulo, opcoes):
    print(f"=== {titulo} ===")
    print(opcoes)
    return input(m + "-> ")

def menu_lista(titulo, dados):
    print(f"\n=== {titulo} ===\n")
    mapa = {}

    for i, item in enumerate(dados, start=1):
        print(f"{i} - {item['nome']}")
        mapa[str(i)] = item["id"]

    escolha = input("\nEscolha -> ")
    return mapa.get(escolha)

# ---------------- ANIMAIS ----------------

def cadastrarAnimal():
    print("1-Nascimento  2-Compra")
    tipo = input("Tipo: ")

    ident = input("Identificador: ")
    raca = input("Raça: ")
    sexo = input("Sexo (M/F): ").upper()
    if sexo not in ["M", "F"]:
        print("Sexo inválido")
        input()
        return
    data = input("Data (DD/MM/YYYY): ")

    if not validar_data(data):
        print("Data inválida")
        input()
        return

    if tipo == "1":
        mae_input = input("Identificador da mãe: ")

        if mae_input == "":
            mae = None
        else:
            mae = get_id_animal(mae_input)

            if not mae:
                print("Mãe não encontrada")
                input()
                return

        insert("""
            INSERT INTO animal
            (identificadorAnimal, racaAnimal,sexoAnimal, dataAdesaoAnimal, idAnimalMae)
            VALUES (:1,:2,:3,TO_DATE(:4,'DD/MM/YYYY'),:5)
        """, [ident, raca, sexo, data, mae])
    else:
        insert("""
            INSERT INTO animal
            (identificadorAnimal, racaAnimal, sexoAnimal, dataAdesaoAnimal)
            VALUES (:1,:2,:3, TO_DATE(:4,'DD/MM/YYYY'))
        """, [ident, raca,sexo, data])

    print("✔ Cadastrado")

def listar_animais_vivos():
    dados = select("""
        SELECT 
            a.identificadorAnimal,
            a.racaAnimal,
            a.sexoAnimal,
            mae.identificadorAnimal,
            TO_CHAR(a.dataAdesaoAnimal,'DD/MM/YYYY')
        FROM animal a
        LEFT JOIN animal mae ON a.idAnimalMae = mae.idAnimal
        WHERE a.dataFalecimentoAnimal IS NULL
    """)

    memoria = [
        {
            "Identificador": d[0],
            "Raça": d[1],
            "Sexo": "Macho" if d[2] == "M" else "Fêmea",
            "Mãe": d[3] if d[3] else "Sem registro",
            "Data Adesão/Nascimento": d[4]
        }
        for d in dados
    ]
    df = pd.DataFrame(memoria)
    print(df if not df.empty else "Sem dados")

def editar_animal():
    ident = input("Identificador: ")

    raca = input("Nova raça: ")
    sexo = input("Sexo (M/F): ").upper()
    data = input("Data (DD/MM/YYYY): ")
    mae_input = input("Identificador da mãe (ou vazio caso não tenha mãe): ")

    if sexo not in ["M", "F"]:
        print("Sexo inválido")
        input()
        return

    if not validar_data(data):
        print("Data inválida")
        input()
        return

    if mae_input == "":
        mae = None
    else:
        mae = get_id_animal(mae_input)
        if not mae:
            print("Mãe não encontrada")
            input()
            return

    update("""
        UPDATE animal
        SET racaAnimal = :1,
            sexoAnimal = :2,
            dataAdesaoAnimal = TO_DATE(:3,'DD/MM/YYYY'),
            idAnimalMae = :4
        WHERE identificadorAnimal = :5
    """, [raca, sexo, data, mae, ident])

    print("✔ Atualizado")
def registrar_morte():
    ident = input("Identificador: ")
    data = input("Data morte: ")
    motivo = input("Motivo: ")

    if not validar_data(data):
        print("Data inválida")
        input()
        return

    idAnimal = get_id_animal(ident)

    if not idAnimal:
        print("Animal não encontrado")
        input()
        return

    # Atualiza animal
    update("""
        UPDATE animal
        SET dataFalecimentoAnimal = TO_DATE(:1,'DD/MM/YYYY'),
            motivoAnimal = :2
        WHERE idAnimal = :3
    """, [data, motivo, idAnimal])

    # Cancela agendamentos futuros  # mudar pra in
    update("""
        UPDATE agendamento
        SET statusAgendamento = 'cancelado'
        WHERE idAnimal = :1
        AND statusAgendamento IN ('atrasado', 'agendado')
    """, [idAnimal])

    print("✔ Morte registrada e agendamentos cancelados")

def excluir_animal():
    ident = input("Identificador: ")

    idAnimal = get_id_animal(ident)

    if not idAnimal:
        print("Animal não encontrado")
        input()
        return

    uso = select("SELECT COUNT(*) FROM agendamento WHERE idAnimal = :1", [idAnimal])[0][0]

    if uso > 0:
        print("Não é possível excluir: animal possui agendamentos")
        input()
        return

    delete("DELETE FROM animal WHERE idAnimal=:1", [idAnimal])
    print("✔ Excluído")

# ---------------- VACINAS ----------------

def cadastrar_vacina():
    nome = input("Nome: ")

    insert("""
        INSERT INTO vacina
        (nomeVacina)
        VALUES (:1)
    """, [nome])

    print("✔ Cadastrada")

def listar_vacinas():
    dados = select("SELECT * FROM vacina")
    df = pd.DataFrame(dados, columns=["ID","Nome"])
    print(df if not df.empty else "Sem dados")

def editar_vacina():
    dados = select("SELECT idVacina, nomeVacina FROM vacina")
    memoria = [{"id": d[0], "nome": d[1]} for d in dados]

    idv = menu_lista("VACINAS", memoria)

    if not idv:
        print("Escolha inválida")
        input()
        return

    nome = input("Novo nome: ")
    update("UPDATE vacina SET nomeVacina=:1 WHERE idVacina=:2", [nome, idv])
    print("✔ Atualizada")

def excluir_vacina():
    dados = select("SELECT idVacina, nomeVacina FROM vacina")
    memoria = [{"id": d[0], "nome": d[1]} for d in dados]

    idv = menu_lista("VACINAS", memoria)

    if not idv:
        print("Escolha inválida")
        input()
        return

    uso = select("SELECT COUNT(*) FROM agendamento WHERE idVacina = :1", [idv])[0][0]

    if uso > 0:
        print("Não é possível excluir: vacina já foi utilizada")
        input()
        return

    delete("DELETE FROM vacina WHERE idVacina=:1", [idv])
    print("✔ Excluída")

# ---------------- AGENDAMENTOS ----------------

def escolher_agendamento(status_permitidos):
    placeholders = ",".join([f":{i+1}" for i in range(len(status_permitidos))])

    dados = select(f"""
        SELECT a.idAgendamento,
            an.identificadorAnimal || ' - ' || v.nomeVacina || ' - ' ||
            TO_CHAR(a.dataAgendamento,'DD/MM/YYYY') || ' - ' || a.statusAgendamento
        FROM agendamento a
        JOIN animal an ON a.idAnimal = an.idAnimal
        JOIN vacina v ON a.idVacina = v.idVacina
        WHERE a.statusAgendamento IN ({placeholders})
    """, status_permitidos)

    memoria = [{"id": d[0], "nome": d[1]} for d in dados]

    if not memoria:
        print("Nenhum agendamento disponível")
        input()
        return None

    return menu_lista("AGENDAMENTOS", memoria)

def agendar_vacina():
    dados = select("SELECT idVacina, nomeVacina FROM vacina")
    memoria = [{"id": d[0], "nome": d[1]} for d in dados]

    idVac = menu_lista("VACINAS", memoria)

    ident = input("Animal: ")
    data = input("Data: ")

    if not validar_data(data):
        print("Data inválida")
        input()
        return

    idAnimal = get_id_animal(ident)

    if not idAnimal:
        print("Animal não encontrado")
        input()
        return

    if not animal_esta_vivo(idAnimal):
        print("Não é possível agendar: animal está morto")
        input()
        return
    
    if data_no_passado(data):
        print("Não é possível agendar para datas passadas")
        input()
        return

    if idVac:
        insert("""
            INSERT INTO agendamento
            (idVacina, idAnimal, dataAgendamento)
            VALUES (:1,:2,TO_DATE(:3,'DD/MM/YYYY'))
        """, [idVac, idAnimal, data])

        print("✔ Agendado")

def listar_agendamentos():
    dados = select("""
        SELECT a.idAgendamento,
               an.identificadorAnimal,
               v.nomeVacina,
               TO_CHAR(a.dataAgendamento,'DD/MM/YYYY'),
               a.statusAgendamento
        FROM agendamento a
        JOIN animal an ON a.idAnimal=an.idAnimal
        JOIN vacina v ON a.idVacina=v.idVacina
    """)

    df = pd.DataFrame(dados, columns=["ID","Animal","Vacina","Data","Status"])
    print(df if not df.empty else "Sem dados")

def marcar_aplicado():
    idg = escolher_agendamento(["agendado", "atrasado"])

    if not idg:
        return

    update("""
        UPDATE agendamento
        SET statusAgendamento='aplicado'
        WHERE idAgendamento=:1
    """, [idg])

    print("✔ Marcado como aplicado")

def marcar_cancelado():
    idg = escolher_agendamento(["agendado", "atrasado"])

    if not idg:
        return

    update("""
        UPDATE agendamento
        SET statusAgendamento='cancelado'
        WHERE idAgendamento=:1
    """, [idg])

    print("✔ Cancelado")


def editar_data_agendamento():
    idg = escolher_agendamento(["agendado", "atrasado"])

    if not idg:
        return

    data = input("Nova data: ")

    if not validar_data(data):
        print("Data inválida")
        input()
        return

    if data_no_passado(data):
        print("Não pode definir data passada")
        input()
        return

    update("""
        UPDATE agendamento
        SET dataAgendamento = TO_DATE(:1,'DD/MM/YYYY'),
        statusAgendamento = 'agendado'
        WHERE idAgendamento = :2
    """,[data,idg])

    print("✔ Data atualizada e status redefinido para agendado")

def excluir_agendamento():
    idg = escolher_agendamento(["agendado","atrasado","cancelado","aplicado"])

    if not idg:
        return 
    
    delete("DELETE FROM agendamento WHERE idAgendamento=:1",[idg])
    print("✔ Excluído")

# ---------------- RELATÓRIO ----------------

def relatorio_atrasados_periodo():
    data_ini, data_fim = pedir_periodo()
    if not data_ini:
        return

    dados = select("""
        SELECT an.identificadorAnimal,
               v.nomeVacina,
               TO_CHAR(a.dataAgendamento,'DD/MM/YYYY')
        FROM agendamento a
        JOIN animal an ON a.idAnimal=an.idAnimal
        JOIN vacina v ON a.idVacina=v.idVacina
        WHERE a.statusAgendamento='atrasado'
        AND a.dataAgendamento BETWEEN 
            TO_DATE(:1,'DD/MM/YYYY') 
            AND TO_DATE(:2,'DD/MM/YYYY')
    """, [data_ini, data_fim])

    df = pd.DataFrame(dados, columns=["Animal","Vacina","Data"])
    print("\nVACINAS ATRASADAS NO PERÍODO:\n")
    print(df if not df.empty else "Nenhuma")

def relatorio_aplicadas_periodo():
    data_ini, data_fim = pedir_periodo()
    if not data_ini:
        return

    dados = select("""
        SELECT an.identificadorAnimal,
               v.nomeVacina,
               TO_CHAR(a.dataAgendamento,'DD/MM/YYYY')
        FROM agendamento a
        JOIN animal an ON a.idAnimal=an.idAnimal
        JOIN vacina v ON a.idVacina=v.idVacina
        WHERE a.statusAgendamento='aplicado'
        AND a.dataAgendamento BETWEEN 
            TO_DATE(:1,'DD/MM/YYYY') 
            AND TO_DATE(:2,'DD/MM/YYYY')
    """, [data_ini, data_fim])

    df = pd.DataFrame(dados, columns=["Animal","Vacina","Data"])
    print("\nVACINAS APLICADAS NO PERÍODO:\n")
    print(df if not df.empty else "Nenhuma")

def relatorio_agendadas_periodo():
    data_ini, data_fim = pedir_periodo()
    if not data_ini:
        return

    dados = select("""
        SELECT an.identificadorAnimal,
               v.nomeVacina,
               TO_CHAR(a.dataAgendamento,'DD/MM/YYYY')
        FROM agendamento a
        JOIN animal an ON a.idAnimal=an.idAnimal
        JOIN vacina v ON a.idVacina=v.idVacina
        WHERE a.statusAgendamento='agendado'
        AND a.dataAgendamento BETWEEN 
            TO_DATE(:1,'DD/MM/YYYY') 
            AND TO_DATE(:2,'DD/MM/YYYY')
    """, [data_ini, data_fim])

    df = pd.DataFrame(dados, columns=["Animal","Vacina","Data"])
    print("\nVACINAS AGENDADAS NO PERÍODO:\n")
    print(df if not df.empty else "Nenhuma")

def relatorio_animais_periodo():
    data_ini, data_fim = pedir_periodo()
    if not data_ini:
        return

    dados = select("""
        SELECT 
            a.identificadorAnimal,
            a.racaAnimal,
            a.sexoAnimal,
            mae.identificadorAnimal,
            TO_CHAR(a.dataAdesaoAnimal,'DD/MM/YYYY'),
            TO_CHAR(a.dataFalecimentoAnimal,'DD/MM/YYYY')
        FROM animal a
        LEFT JOIN animal mae ON a.idAnimalMae = mae.idAnimal
        WHERE a.dataAdesaoAnimal BETWEEN 
            TO_DATE(:1,'DD/MM/YYYY') 
            AND TO_DATE(:2,'DD/MM/YYYY')
        ORDER BY a.dataAdesaoAnimal
    """, [data_ini, data_fim])

    memoria = [
        {
            "Animal": d[0],
            "Raça": d[1],
            "Sexo": "Macho" if d[2] == "M" else "Fêmea",
            "Mãe": d[3] if d[3] else "Sem registro",
            "Data Cadastro": d[4],
            "Status": f"Morto em {d[5]}" if d[5] else "Vivo"
        }
        for d in dados
    ]

    df = pd.DataFrame(memoria)

    print("\n=== ANIMAIS ADQUIRIDOS/NASCIDOS NO PERÍODO ===\n")
    print(df if not df.empty else "Nenhum")

def relatorio_animais_mortos():
    dados = select("""
        SELECT 
            a.identificadorAnimal,
            a.racaAnimal,
            a.sexoAnimal,
            mae.identificadorAnimal,
            TO_CHAR(a.dataAdesaoAnimal,'DD/MM/YYYY'),
            TO_CHAR(a.dataFalecimentoAnimal,'DD/MM/YYYY'),
            a.motivoAnimal
        FROM animal a
        LEFT JOIN animal mae ON a.idAnimalMae = mae.idAnimal
        WHERE a.dataFalecimentoAnimal IS NOT NULL
        ORDER BY a.dataFalecimentoAnimal DESC
    """)

    memoria = [
        {
            "Animal": d[0],
            "Raça": d[1],
            "Sexo": "Macho" if d[2] == "M" else "Fêmea",
            "Mãe": d[3] if d[3] else "Sem registro",
            "Entrada": d[4],
            "Data Morte": d[5],
            "Motivo": d[6] if d[6] else "Não informado"
        }
        for d in dados
    ]

    df = pd.DataFrame(memoria)

    print("\n=== ANIMAIS MORTOS (DETALHADO) ===\n")
    print(df if not df.empty else "Nenhum")

def relatorio_qtd_vacinas():
    dados = select("""
        SELECT v.nomeVacina, COUNT(*)
        FROM agendamento a
        JOIN vacina v ON a.idVacina = v.idVacina
        WHERE a.statusAgendamento = 'aplicado'
        GROUP BY v.nomeVacina
    """)

    df = pd.DataFrame(dados, columns=["Vacina","Quantidade"])
    print("\nTOTAL DE VACINAS APLICADAS:\n")
    print(df if not df.empty else "Nenhum dado")

def relatorio_historico_animal():
    ident = input("Identificador do animal: ")

    dados = select("""
        SELECT v.nomeVacina,
               TO_CHAR(a.dataAgendamento,'DD/MM/YYYY'),
               a.statusAgendamento
        FROM agendamento a
        JOIN vacina v ON a.idVacina=v.idVacina
        JOIN animal an ON a.idAnimal=an.idAnimal
        WHERE an.identificadorAnimal = :1
    """, [ident])

    df = pd.DataFrame(dados, columns=["Vacina","Data","Status"])
    print(f"\nHISTÓRICO DE VACINAS DO ANIMAL {ident}:\n")
    print(df if not df.empty else "Sem registros")

def relatorio_sem_vacina():
    dados = select("""
        SELECT a.identificadorAnimal
        FROM animal a
        WHERE a.dataFalecimentoAnimal IS NULL
        AND NOT EXISTS (
            SELECT 1
            FROM agendamento ag
            WHERE ag.idAnimal = a.idAnimal
            AND ag.statusAgendamento IN ('aplicado', 'agendado')
        )
    """)

    df = pd.DataFrame(dados, columns=["Animal"])
    print("\nANIMAIS SEM VACINA APLICADA OU AGENDADA:\n")
    print(df if not df.empty else "Todos os animais vivos com vacinas aplicadas ou agendadas")

def relatorio_geral():
    total = select("SELECT COUNT(*) FROM animal")[0][0]
    vivos = select("SELECT COUNT(*) FROM animal WHERE dataFalecimentoAnimal IS NULL")[0][0]
    mortos = select("SELECT COUNT(*) FROM animal WHERE dataFalecimentoAnimal IS NOT NULL")[0][0]

    print("\n=== RESUMO ===")
    print(f"Total animais: {total}")
    print(f"Vivos: {vivos}")
    print(f"Mortos: {mortos}")

# -------------- ARQUIVO txt --------------

def gerar_relatorio_txt():
    nome_arquivo = "arquivos/relatorio_fazenda.txt"

    with open(nome_arquivo, "w", encoding="utf-8") as f:

        f.write("===== RELATÓRIO COMPLETO DA FAZENDA =====\n\n")

        # ---------------- ANIMAIS ----------------
        dados = select("""
            SELECT 
                a.identificadorAnimal,
                a.racaAnimal,
                a.sexoAnimal,
                mae.identificadorAnimal,
                TO_CHAR(a.dataAdesaoAnimal,'DD/MM/YYYY'),
                TO_CHAR(a.dataFalecimentoAnimal,'DD/MM/YYYY'),
                a.motivoAnimal
            FROM animal a
            LEFT JOIN animal mae ON a.idAnimalMae = mae.idAnimal
        """)
        f.write("=== ANIMAIS ===\n")

        for d in dados:
            ident = d[0]
            raca = d[1]
            sexo = "Macho" if d[2] == "M" else "Fêmea"
            mae = d[3] if d[3] else "Sem registro"
            data_adesao = d[4]
            data_morte = d[5]
            motivo = d[6]

            if data_morte:
                status = f"MORTO em {data_morte} | Motivo: {motivo}"
            else:
                status = "VIVO"

            f.write(
                f"ID: {ident} | Raça: {raca} | Sexo: {sexo} | "
                f"Mãe: {mae} | Entrada: {data_adesao} | {status}\n"
            )

        # ---------------- VACINAS ----------------
        dados = select("SELECT nomeVacina FROM vacina")

        f.write("\n=== VACINAS ===\n")
        for d in dados:
            f.write(f"Vacina: {d[0]}\n")

        # ---------------- AGENDAMENTOS ----------------
        dados = select("""
            SELECT an.identificadorAnimal, v.nomeVacina,
                   TO_CHAR(a.dataAgendamento,'DD/MM/YYYY'),
                   a.statusAgendamento
            FROM agendamento a
            JOIN animal an ON a.idAnimal=an.idAnimal
            JOIN vacina v ON a.idVacina=v.idVacina
        """)

        f.write("\n=== AGENDAMENTOS ===\n")
        for d in dados:
            f.write(f"{d[0]} | {d[1]} | {d[2]} | {d[3]}\n")

    print(f"\n✔ Relatório salvo em: {nome_arquivo}")


# -------------- BACKUP json --------------

def exportar_json():
    dados = select("""
        SELECT an.identificadorAnimal,
               an.racaAnimal,
               v.nomeVacina,
               TO_CHAR(a.dataAgendamento,'DD/MM/YYYY'),
               a.statusAgendamento
        FROM agendamento a
        JOIN animal an ON a.idAnimal=an.idAnimal
        JOIN vacina v ON a.idVacina=v.idVacina
    """)

    lista = []
    for d in dados:
        lista.append({
            "animal": d[0],
            "raca": d[1],
            "vacina": d[2],
            "data": d[3],
            "status": d[4]
        })

    with open("arquivos/dados_fazenda.json", "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=4, ensure_ascii=False)

    print("✔ JSON exportado: arquivos/dados_fazenda.json")

# ---------------- SISTEMA ----------------

while True:
    atualizar_atrasados()
    os.system('cls')
    op = menu_principal()

    match op:

        case "1":
            while True:
                os.system('cls')
                a = menu_secundario("ANIMAIS", """
                1 - Cadastrar
                2 - Listar vivos
                3 - Editar
                4 - Registrar morte
                5 - Excluir
                6 - Voltar
                """)

                match a:
                    case "1": cadastrarAnimal()
                    case "2": listar_animais_vivos()
                    case "3": editar_animal()
                    case "4": registrar_morte()
                    case "5": excluir_animal()
                    case "6": break

                input("\nENTER")

        case "2":
            while True:
                os.system('cls')
                v = menu_secundario("VACINAS", """
                1 - Cadastrar
                2 - Listar
                3 - Editar
                4 - Excluir
                5 - Voltar
                """)

                match v:
                    case "1": cadastrar_vacina()
                    case "2": listar_vacinas()
                    case "3": editar_vacina()
                    case "4": excluir_vacina()
                    case "5": break

                input("\nENTER")

        case "3":
            while True:
                os.system('cls')
                ag = menu_secundario("AGENDAMENTOS", """
                1 - Agendar
                2 - Listar
                3 - Marcar aplicado
                4 - marcar cancelado
                5 - Editar data
                6 - Excluir
                7 - Voltar
                """)

                match ag:
                    case "1": agendar_vacina()
                    case "2": listar_agendamentos()
                    case "3": marcar_aplicado()
                    case "4": marcar_cancelado()
                    case "5": editar_data_agendamento()
                    case "6": excluir_agendamento()
                    case "7": break

                input("\nENTER")

        case "4":
            while True:
                os.system('cls')
                ag = menu_secundario("RELATÓRIOS", """
                1 - Atrasados por período
                2 - Aplicadas por período
                3 - Agendadas por período
                4 - Animais adquiridos/nascidos por período
                5 - Animais mortos
                6 - Total de vacinas aplicadas
                7 - Histórico de vacina por animal
                8 - Animais sem vacina aplicada ou agendada 
                9 - Resumo geral
                10 - Exportar relatório TXT 
                11 - Exportar JSON
                12 - Voltar
                """)

                match ag:
                    case "1": relatorio_atrasados_periodo()
                    case "2": relatorio_aplicadas_periodo()
                    case "3": relatorio_agendadas_periodo()
                    case "4": relatorio_animais_periodo()
                    case "5": relatorio_animais_mortos()
                    case "6": relatorio_qtd_vacinas()
                    case "7": relatorio_historico_animal()
                    case "8": relatorio_sem_vacina()
                    case "9": relatorio_geral()
                    case "10": gerar_relatorio_txt()
                    case "11": exportar_json()
                    case "12": break

                input("\nENTER")

        case "5":
            break

        case _:
            print("Opção inválida")
            input("\nENTER")

c.close()
conn.close()
print("Sistema encerrado.")