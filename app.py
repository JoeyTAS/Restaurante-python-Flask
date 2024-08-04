from flask import Flask, render_template, request, redirect, make_response
import os
import json


app = Flask(__name__)

RutaLog = os.path.dirname(os.path.abspath(__file__))
RutaCre = os.path.join(RutaLog, "credenciales.txt")
RutaDesa = os.path.join(RutaLog, "desayunos.json")
RutaMen = os.path.join(RutaLog, "menus.json")
RutaCen = os.path.join(RutaLog, "cena.json")
RutaPed = os.path.join(RutaLog, "pedidos.json")
def CargarCen():
    try:
        with open(RutaCen, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    
def CargarMen():
    try:
        with open(RutaMen, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
credenciales = {
    "ADMIN": "123",
    "CLIENTE": "456",
    "EMPLEADO": "789"
}

def RegistroUsuario():
    try:
        with open(RutaCre, "r") as file:
            for line in file:
                var, contra = line.strip().split(":")
                credenciales[var] = contra
    except FileNotFoundError:
        pass

RegistroUsuario()

def GuardarUsuarios():
    with open(RutaCre, "w") as file:
        for var, contra in credenciales.items():
            file.write(f"{var}:{contra}\n")

def Salu():
    mensaje = "BIENVENIDO"
    mensaje2 = "RESTAURANT RICO MENU SAC"
    dicre = "AV AREQUIPA N° 567 CERCADO AREQUIPA"
    return mensaje, mensaje2, dicre

pedidos = []
desayunos_precios = []
cenas_precios = []

def CargarDesayunos():
    try:
        with open(RutaDesa, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def CargarPedidos():
    try:
        with open(RutaPed, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
def LimpiarPedidos():
    global pedidos
    pedidos = []
    with open(RutaPed, 'w') as file:
        json.dump(pedidos, file)
cenas_precios = CargarCen()
desayunos_precios = CargarDesayunos()
pedidos = CargarPedidos()

@app.route('/')
def inicio():
    global pedidos, desayunos_precios, cenas_precios

    pedidos = []
    desayunos_precios = []
    cenas_precios = []

    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    global pedidos, desayunos_precios, cenas_precios
    pedidos = []
    desayunos_precios = []
    cenas_precios  = []

    var = request.form['usuario']
    contra = request.form['contrasena']

    if var in credenciales and contra == credenciales[var]:
        mensaje, mensaje2, dicre = Salu()
        return render_template('bienvenido.html', mensaje=mensaje, usuario=var, mensaje2=mensaje2, dicre=dicre)
    else:
        mensaje = "Intenta otra vez"
        return render_template('resultado.html', mensaje=mensaje)

@app.route('/bienvenido')
def bienvenido():
    global pedidos
    pedidos = []
    var = request.args.get('usuario')
    return render_template('bienvenido.html', usuario=var)

@app.route('/crear-cuenta', methods=['POST'])
def crear_cuenta():
    var = request.form['usuario']
    contra = request.form['contrasena']
    contra = str(contra)
    if var not in credenciales:
        credenciales[var] = contra
        GuardarUsuarios()
        mensaje = "Cuenta creada exitosamente"
    else:
        mensaje = "El nombre de usuario ya existe"
    return render_template('resultado.html', mensaje=mensaje)
@app.route('/agregar_pedido', methods=['POST'])
def agregar_pedido():
    global pedidos, desayunos_precios, cenas_precios

    pedido = {}
    total = 0.0
    precios = {}
    for desayuno in desayunos_precios:
        precios[desayuno['nombre']] = desayuno['precio']

    for desayuno in desayunos_precios:
        desayuno_id = str(desayuno['id'])
        cantidad = int(request.form.get(f'cantidad_{desayuno_id}', 0))
        if cantidad > 0:
            subtotal = cantidad * precios.get(desayuno['nombre'], 0)
            pedido[desayuno['nombre']] = {'cantidad': cantidad, 'subtotal': subtotal}
            total += subtotal

    pedidos.append(pedido)

    with open(RutaPed, 'w') as file:
        json.dump(pedidos, file)

    return redirect('/estado_pedido')

@app.route('/carta_desayuno')
def carta_desayuno():
    global desayunos_precios
    desayunos_precios = CargarDesayunos()
    return render_template('carta_desayuno.html', desayunos_precios=desayunos_precios)
@app.route('/carta_menus')
def carta_menus():
    global desayunos_precios
    desayunos_precios = CargarMen()
    return render_template('carta_menus.html', desayunos_precios=desayunos_precios)
@app.route('/carta_cen')
def carta_cena():
    global cenas_precios
    cenas_precios = CargarCen()
    return render_template('carta_cenas.html', cenas_precios=cenas_precios)

@app.route('/agregar_cena_pedido', methods=['POST'])
def agregar_cena_pedido():
    global pedidos, desayunos_precios, cenas_precios

    if not cenas_precios:
        cenas_precios = CargarCen()

    if len(pedidos) > 0:
        pedido_actual = pedidos[-1]
    else:
        pedido_actual = {}

    for cena in cenas_precios:
        cantidad = int(request.form.get(f'cantidad_{cena["id"]}', 0))
        if cantidad > 0:
            pedido_actual[cena['id']] = {'nombre': cena['nombre'], 'cantidad': cantidad, 'precio': cena['precio']}

    pedidos.append(pedido_actual)
    
    subtotal_pedido, igv_pedido, total_pedido = calcular_totales()
    return render_template('estado_pedido.html', pedidos=pedidos, subtotal_pedido=subtotal_pedido, igv_pedido=igv_pedido, total_pedido=total_pedido)




@app.route('/estado_pedido')
def estado_pedido():
    global pedidos, desayunos_precios

    try:
        if not pedidos:
            pedidos = CargarPedidos()

        if not desayunos_precios:
            desayunos_precios = CargarDesayunos()

        subtotal_pedido = 0
        precios = {}
        for desayuno in desayunos_precios:
            precios[desayuno["nombre"]] = desayuno["precio"]
            cantidad = pedidos[-1].get(desayuno["nombre"], {}).get("cantidad", 0)
            subtotal_pedido += desayuno["precio"] * cantidad

        igv_pedido = subtotal_pedido * 0.18
        total_pedido = subtotal_pedido + igv_pedido

        # Verificar si no hay pedidos
        if not pedidos:
            mensaje = "Aún no has realizado ningún pedido."
            return render_template('estado_pedido.html', mensaje=mensaje,
                                   subtotal_pedido=0, igv_pedido=0, total_pedido=0)

        return render_template('estado_pedido.html', pedidos=pedidos, precios=precios,
                               subtotal_pedido=subtotal_pedido, igv_pedido=igv_pedido,
                               total_pedido=total_pedido, mensaje=None)

    except Exception as e:
        print("Error:", e)
        mensaje = "Ha ocurrido un error al cargar el estado del pedido."
        return render_template('estado_pedido.html', mensaje=mensaje,
                               subtotal_pedido=0, igv_pedido=0, total_pedido=0)






@app.route('/enviar_pedido', methods=['POST'])
def enviar_pedido():
    global pedidos, desayunos_precios

    if not desayunos_precios:
        desayunos_precios = CargarDesayunos()

    if len(pedidos) > 0:
        ultimo_pedido = pedidos[-1]
    else:
        ultimo_pedido = {}

    if not any(ultimo_pedido.values()):
        mensaje = "No has seleccionado ningún ítem en el pedido."
        return render_template('estado_pedido.html', mensaje=mensaje,
                               subtotal_pedido=0, igv_pedido=0, total_pedido=0)

    subtotal_pedido, igv_pedido, total_pedido = calcular_totales()

    # Agregar lógica para borrar el pedido actual
    pedidos.pop()  # Esto eliminará el último pedido de la lista

    return render_template('recibo.html', subtotal_pedido=subtotal_pedido, igv_pedido=igv_pedido, total_pedido=total_pedido)




@app.route('/tracciones_pedido', methods=['POST'])
def tracciones_pedido():
    global pedidos, desayunos_precios
    pedido_idx = int(request.form.get('pedido_idx'))
    pedido_actual = pedidos[pedido_idx]
    desayuno_id = request.form.get('desayuno_id')
    cantidad_actual = pedido_actual.get(desayuno_id, {}).get('cantidad', 0)
    nueva_cantidad = int(request.form.get(f'cantidad_{desayuno_id}', cantidad_actual))
    if nueva_cantidad == 0:
        del pedido_actual[desayuno_id]
    else:
        pedido_actual[desayuno_id]['cantidad'] = nueva_cantidad
    pedidos[pedido_idx] = pedido_actual
    return redirect('/estado_pedido')

def generar_recibo():
    global pedidos, desayunos_precios
    pedido_idx = int(request.form.get('pedido_idx'))
    pedido_actual = pedidos[pedido_idx]

    for desayuno_id in request.form:
        if desayuno_id.startswith('cantidad_'):
            desayuno_id = desayuno_id.replace('cantidad_', '')
            cantidad_actual = pedido_actual.get(desayuno_id, {}).get('cantidad', 0)
            nueva_cantidad = int(request.form.get('cantidad_' + desayuno_id, cantidad_actual))
            pedido_actual[desayuno_id] = {'cantidad': nueva_cantidad}

    if not desayunos_precios:
        desayunos_precios = CargarDesayunos()

    subtotal_pedido, igv_pedido, total_pedido = calcular_totales()
    ultimo_pedido = pedidos[-1] if pedidos else {}

    # Imprimir para depuración
    print("pedidos:", pedidos)
    print("ultimo_pedido:", ultimo_pedido)

    return render_template('recibo.html', ultimo_pedido=ultimo_pedido, subtotal_pedido=subtotal_pedido, igv_pedido=igv_pedido, total_pedido=total_pedido)



@app.route('/cerrar_sesion')
def cerrar_sesion():
    LimpiarPedidos()
    return render_template('cerrar_sesion.html')


@app.after_request
def agregar_encabezados(resp):
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


def calcular_totales():
    global pedidos, desayunos_precios

    subtotal_pedido = 0
    precios = {}
    for desayuno in desayunos_precios:
        precios[desayuno["nombre"]] = desayuno["precio"]
        cantidad = pedidos[-1].get(desayuno["nombre"], {}).get("cantidad", 0)
        subtotal_pedido += desayuno["precio"] * cantidad
    igv_pedido = subtotal_pedido * 0.18
    total_pedido = subtotal_pedido + igv_pedido
    return subtotal_pedido, igv_pedido, total_pedido


if __name__ == '__main__':
    app.run(debug=True)






