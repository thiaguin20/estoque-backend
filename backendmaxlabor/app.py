from flask import Flask, request, jsonify
import psycopg2
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 🔗 Conexão com o banco do Supabase
conn = psycopg2.connect(
    host="db.zzloppdbpvhpumsnhbuq.supabase.co",
    database="postgres",
    user="postgres",
    password="SenhaForte1@",
    port="5432"
)

# 🧾 Listar todos os itens do estoque
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

# ⬆️ Entrada de item
@app.route('/entrada', methods=['POST'])
def entrada():
    data = request.get_json()
    cur = conn.cursor()
    cur.execute("UPDATE itens SET quantidade = quantidade + %s WHERE id = %s;", (data['quantidade'], data['id']))
    cur.execute("INSERT INTO movimentacoes (item_id, tipo, quantidade) VALUES (%s, 'entrada', %s);", (data['id'], data['quantidade']))
    conn.commit()
    cur.close()
    return jsonify({"message": "Entrada registrada!"})

# ⬇️ Saída de item
@app.route('/saida', methods=['POST'])
def saida():
    data = request.get_json()
    cur = conn.cursor()
    cur.execute("UPDATE itens SET quantidade = quantidade - %s WHERE id = %s;", (data['quantidade'], data['id']))
    cur.execute("INSERT INTO movimentacoes (item_id, tipo, quantidade) VALUES (%s, 'saida', %s);", (data['id'], data['quantidade']))
    conn.commit()
    cur.close()
    return jsonify({"message": "Saída registrada!"})

# 🚀 Rodar o servidor
if __name__ == '__main__':
    app.run(debug=True)
