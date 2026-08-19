from wsgiref.simple_server import make_server

def aplicacao_web(environ, start_response):
    produtos = [
        {'nome': 'Notebook', 'valor': 7499.99},
        {'nome': 'Mouse', 'valor': 125.99},
        {'nome': 'Teclado', 'valor': 450.99},
        {'nome': 'Monitor', 'valor': 2100.99},
    ]
    
    linhas_html = ''
    for produto in produtos:
        linhas_html += f'<li>{produto['nome']} - R$ {produto['valor']}</li>'
    
    start_response('200 Ok', [('Content-type','text/html;charset-utf-8')])
    
    with open('index.html','r',encoding='utf-8') as f:
        html = f.read()
        
    html_final = html.replace('{{PRODUTOS}}',linhas_html)
    
    return [html_final.encode('utf-8')]

# host,porta,retorno do server(aplicacao)
make_server('',8001,aplicacao_web).serve_forever()

# Utilizando padrão PEP3333 (Python enhancement proposal), 
# padrão que separa server da aplicacao