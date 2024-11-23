from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
import pyodbc
import pandas as pd

app = Flask(__name__)
app.secret_key = 'chavesecreta'

# Configuração da string de conexão

conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=database\db_geos.accdb;'
)

#conectando o ao banco de dados
conn = pyodbc.connect(conn_str)


# Variaveis globais
sites = ["Geral", "Site 2", "Site 3"]


# * PAGINAS *
# INDEX "/"
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('menu.html')


# CADASTRO "/cadastro"
@app.route('/cadastro',methods=['GET', 'POST'])
def cadastro():
    df_selecionar = pd.DataFrame(columns=['descricao', 'tamanho', 'midia','fabricante','qnt_disp','local','unidade'])
    data_reserva = pd.DataFrame(columns=['os', 'descricao', 'tamanho','fabricante','qntd', 'acao', 'local'])
    selected_site = None
    if request.method == 'POST':
        selected_site = request.form.get('site')
        selected_local = request.form.get('local')
    return render_template('cadastro.html', 
                           data=df_selecionar,
                           data_reserva=data_reserva,
                           sites=sites,
                           selected_site=selected_site,
                        )



# ESTOQUE "/estoque"
# todo: FUNÇÕES DE FORMULARIOS
@app.route('/estoque',methods=['GET', 'POST'])
def estoque():
    #criação do dataframe
    df = pd.DataFrame(columns=['descricao', 'tamanho', 'midia','fabricante','qnt_fis','qnt_disp','local','unidade','categoria'])
    selected_site = None
    ind_estoques = ['Geral', 'SEM ESTOQUE', 'INDISPONIVEL', 'DISPONIVEL']
    categorias = get_categorias()
    if request.method == 'POST':
        selected_site = request.form.get('site')
        selected_ind_estoque = request.form.get('ind_estoque')
        selected_categoria= request.form.get('categoria')
        selected_local = request.form.get('local')
        
        # PRINTS DE DEBUG
        print(f'selected_site: {selected_site}')
        print(f'selected_local: {selected_local}')
        print(f'selected_categoria: {selected_categoria}')
        print(f'selected_ind_estoque: {selected_ind_estoque}')
        
    return render_template('estoque.html',
                            data=df,
                            sites=sites,
                            selected_site=selected_site,
                            ind_estoques=ind_estoques,
                            categorias=categorias,
                        )



# MOVIMENTAÇÂO "/movimentacao"
@app.route('/movimentacao',methods=['GET', 'POST'])
def movimentacao():
    df = pd.DataFrame(columns=['descricao', 'tamanho', 'quantidade','data','tipo','atendeu','ocorrencia'])
    selected_site = None
    selected_local = None
    date_range = None
    categorias = get_categorias()
    if request.method == 'POST':
        selected_site = request.form.get('site')
        selected_local = request.form.get('local')
        date_range = request.form.get('dateRange')
        selected_categoria= request.form.get('categoria')
        
        
        if date_range:
            data_inicial, data_final = parse_date_range(date_range)
        
        # PRINTS DE DEBUG
        print(f'selected_site: {selected_site}')
        print(f'selected_local: {selected_local}')
        print(f'date_range: {date_range}')
        print(f'data_inicial: {data_inicial}')
        print(f'data_final: {data_final}')
        print(f'selected_categoria: {selected_categoria}')
        
    
    return render_template('movimentacao.html', 
                            data=df,
                            sites=sites,
                            selected_site=selected_site,
                            selected_local=selected_local,
                            date_range=date_range,
                            categorias=categorias,                    
                        )


# PROJETOS "/projetos"
@app.route('/projetos',methods=['GET', 'POST'])
def projetos():
    return render_template('projetos.html')



# RELATORIOS "/relatorios"
@app.route('/relatorio',methods=['GET', 'POST'])
def relatorios():
    return render_template('relatorios.html')


# Funcao para buscar os locais de estoque de acordo com o site selecionado
# Estoque -> AJAX (APOS SELECIONAR O SITE)
@app.route('/get_locais', methods=['POST'])
def get_locais():
    site_selecionado = request.json.get('site')
    if site_selecionado == 'Geral':
        return jsonify({"locais": ["Geral"]})
    if not site_selecionado:
        return jsonify({"error": "Nenhum site selecionado"}), 400
    
    # Obtenha o id_unidade com base no site selecionado
    id_site = get_id_site(site_selecionado)
    if id_site:
        locais = get_estoques_por_id_unidade(id_site)
        return jsonify({"locais": locais})
    else:
        return jsonify({"error": "Site não encontrado"}), 404

    
# Função para separar a data inicial e final de um intervalo de datas
def parse_date_range(date_range):
    """
    Recebe um intervalo de datas (ou uma única data) e retorna as datas separadas.
    :param date_range: String com o intervalo de datas no formato "dd/mm/yyyy to dd/mm/yyyy" ou "dd/mm/yyyy".
    :return: Uma tupla (data_inicial, data_final), onde cada elemento é uma string no formato "dd/mm/yyyy".
    """
    if " to " in date_range:  # Intervalo de datas
        data_inicial, data_final = date_range.split(" to ")
        return data_inicial.strip(), data_final.strip()
    else:  # Apenas uma data
        return date_range.strip(), None


#   * SELECTS *
def get_id_site(nome_unidade):
    try:
        query = "SELECT id_unidade FROM Unidades WHERE nome_unidade = ?"
        cursor = conn.cursor()
        cursor.execute(query, (nome_unidade,))
        result = cursor.fetchone()
        if result:
            return result[0]  # Retorna o id_unidade
        else:
            return None  # Caso o nome_unidade não seja encontrado
    except Exception as e:
        print(f"Erro ao buscar id_unidade: {e}")
        return None

# Função para buscar os locais de estoque de acordo com o id_unidade
def get_estoques_por_id_unidade(id_unidade):
    try:
        query = "SELECT nome_local FROM LocalEstoque WHERE id_unidade = ?"
        cursor = conn.cursor()
        cursor.execute(query, (id_unidade,))
        results = cursor.fetchall()
        
        # Retorna uma lista de estoques (nome_local)
        return [row[0] for row in results] if results else []
    except Exception as e:
        print(f"Erro ao buscar estoques para id_unidade {id_unidade}: {e}")
        return []

# Consulta para buscar todas as categorias
def get_categorias():
    try:
        query = "SELECT Categorias.nome_categoria FROM Categorias;"
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Retorna uma lista de estoques (nome_local)
        return [row[0] for row in results] if results else []
    except Exception as e:
        return []
    
#Funcao main - roda o projeto
if __name__ == '__main__':
    app.run(debug=True)
    
