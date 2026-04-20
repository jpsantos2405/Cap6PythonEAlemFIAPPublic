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

