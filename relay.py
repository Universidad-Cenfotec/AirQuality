# Importanción de librerias.
import board
import time
from ideaboard import IdeaBoard

# Creación de la instancia ib.
ib = IdeaBoard()

# Utiliza el pin IO27.
salida = ib.DigitalOut(board.IO27)
while True:
    # Enciende.
    salida.value = True
    print("Esta encendido")
    time.sleep(5)
    # Apaga.
    salida.value = False
    print("Esta apagado")
    time.sleep(5)
    
# Nota: En caso de hacer un loop, poner un tiempo de espera razonable,
# de otra manera se podría generar un corto circuito.