from flask import Flask, request, jsonify
import psycopg2
from flask_cors import CORS
import socket

app = Flask(__name__)
CORS(app)

# ⚙️ Forçar conexão IPv4 (corrige erro "Network is unreachable" no Render)
def connect_ipv4():
    original_getaddrinfo = socket.getaddrinfo
    def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
        return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    socket.getaddrinfo = getaddrinfo_ipv4

connect_ipv4()

# 🔗 Conexão com o banco Supabase
conn = psycopg2.connect(
    host="db.zzloppdbpvhpumsnhbuq.supabase.co",
    database="postgres",
    user="postgres",
    password="SenhaForte1@",
    port="5432"
)

# 🧾 Listar todos os itens
@app.route('/itens', methods=['GET'])
def listar_itens():
    cur = conn.cursor()
    cur.execute("SELECT id, nome, quantidade, minimo, unidade FROM itens ORDER BY id;")
    rows = cur.fetchall()
    cur.close()
    itens = []
    for r in rows:
        status = "baixo" if r[2] <= r[3] else "ok"
        itens.append({
            "id": r[0],
            "nome": r[1],
            "quantidade": r[2],
            "minimo": r[3],
            "unidade": r[4],
            "status": status
        })
    return jsonify(itens)

# ➕ Adicionar novo item
@app.route('/itens', methods=['POST'])
def adicionar_item():
    data = request.get_json()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO itens (nome, quantidade, minimo, unidade)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """, (data['nome'], data['quantidade'], data['minimo'], data.get('unidade', 'un')))
    conn.commit()
    new_id = cur.fetchone()[0]
    cur.close()
    return jsonify({"id": new_id, "message": "Item adicionado com sucesso!"})

# 🗑️ Deletar item
@app.route('/itens/<int:item_id>', methods=['DELETE'])
def deletar_item(item_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM movimentacoes WHERE item_id = %s;", (item_id,))
    cur.execute("DELETE FROM itens WHERE id = %s;", (item_id,))
    conn.commit()
    cur.close()
    return jsonify({"message": "Item excluído com sucesso!"})

# ⬆️ Registrar entrada
@app.route('/entrada', methods=['POST'])
def entrada():
    data = request.get_json()
    cur = conn.cursor()
    cur.execute("UPDATE itens SET quantidade = quantidade + %s WHERE id = %s;", (data['quantidade'], data['id']))
    cur.execute("INSERT INTO movimentacoes (item_id, tipo, quantidade) VALUES (%s, 'entrada', %s);", (data['id'], data['quantidade']))
    conn.commit()
    cur.close()
    return jsonify({"message": "Entrada registrada!"})

# ⬇️ Registrar saída
@app.route('/saida', methods=['POST'])
def saida():
    data = request.get_json()
    cur = conn.cursor()
    cur.execute("UPDATE itens SET quantidade = quantidade - %s WHERE id = %s;", (data['quantidade'], data['id']))
    cur.execute("INSERT INTO movimentacoes (item_id, tipo, quantidade) VALUES (%s, 'saida', %s);", (data['id'], data['quantidade']))
    conn.commit()
    cur.close()
    return jsonify({"message": "Saída registrada!"})

# 🚀 Rodar servidor
if __name__ == '__main__':
    app.run(debug=True)
