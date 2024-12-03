#coding: UTF-8


"""_summary_

Formato das entradas:
    _type_: nomeProcesso|PID|tempoDeExecução|prioridade (ou bilhetes)|qtdeMemoria|sequênciaAcessoPaginasProcesso|chanceRequisitarES
        
        onde:
       
        - chanceRequisitarES informa a chance que o processo tem de requisitar uma operação de E/S durante a sua fração de CPU
        
    nos dispositivos: 
    
    _type_:
        idDispositivo|numUsosSimultaneos|tempoOperação
        
        onde:
        - idDispositivo é o identificador do dispositivo de E/S
        - numUsosSimultaneos representa a quatidade de processos que podem fazer uso daquele dispositivo de forma simultânea
        - tempoOperação indica quanto tempo o dispositivo demora para executar uma operação de E/S
        
        
    A cada vez que for trocar o processo em execução na CPU, o seu programa deverá mostrar o estado dos processos. Isto é, indicar o processo que está em execução, o(s) processo(s) 
    em estado pronto e o(s) processo(s) bloqueados. Para todos deve ser informado o tempo de CPU restante para sua conclusão. Para os processos em estado bloqueado, também deverá 
    ser informado o dispositivo que está sendo utilizado/aguardado. Além disso, o seu programa deverá mostrar a lista dos dispositivos existentes, o seu estado e os processos que 
    estão fazendo uso ou esperando para fazer uso.

    Toda vez que um processo for escolhido para ir para a CPU, você deverá determinar, baseado na probabilidade informada, se ele irá solicitar uma operação de E/S naquele ciclo. 
    Caso o processo solicite uma operação de E/S, você também deverá determinar (aleatoriamente) qual dispositivo será solicitado para uso e, em qual momento da fatia isto ocorrerá. 
    Observe que os dispositivos possuem um limite de processos que podem utilizá-los por vez. Caso o processo escolha utilizar um dispositivo que já está em uso por outro processo, 
    este deverá entrar em uma "fila de espera" do dispositivo. Enquanto o processo está realizando uma operação de E/S ou aguardando para começar sua operação de E/S, ele não poderá 
    ser escalonado para a CPU. Nota-se, porém, que havendo outros processos em estado "pronto", estes devem prosseguir sua execução normalmente de acordo com a política de escalonamento.

    Ao final da execução, o seu algoritmo deverá mostrar quanto tempo um processo demorou para ser executado, isto é, desde o momento em que foi criado até o momento em que foi 
    concluído. Também deve informar o tempo em que esteve em pronto e o tempo em que esteve em estado bloqueado.
"""

import sys
import threading
from tqdm import tqdm
import time
import random
import time
try:
    from tqdm import tqdm
except:
    print("Modulo 'tqdm' nao instalado.\nTente pip install tqdm")
from queue import Queue

class Processo:
    def __init__(self, name, PID, time_exec, prioridade, qnt_memoria, pages_sequence, chance_to_request ):
        """Inicializa os atributos de um processo."""
        self.name = name
        self.PID = int(PID) 
        self.time_exec = int(time_exec)
        self.prioridade = int(prioridade)
        self.qnt_memoria = int(qnt_memoria)
        self.pages_sequence = [pages_sequence]
        self.chance_to_request = int(chance_to_request)
        self.time_processed = 0
        self.finished = None
        self.numeros = []
        self.state = None
    
    def processa(self,quantum):
        """Imita o tempo gasto pelo processador diminuindo o tempo de execucao
        do processo.
        """
        
        for i in tqdm(range(quantum)):   
            #sys.stdout.write("\r{0}>".format("="*i))
            #sys.stdout.flush()
            time.sleep(0.5)
        
        self.time_processed = self.time_processed+quantum
        self.time_exec = self.time_exec-quantum
    
class Device:
    def __init__(self, id, sim_uses,time_operation ):
        self.id = str(id)
        self.simultaneous_uses = int(sim_uses)
        self.time_operation = int(time_operation) 
        self.processes_using = int(0)
        self.queue = Queue()
        self.in_use = threading.Lock()  # Controle de uso do dispositivo

    def start_operation(self, processo):
        with self.lock:
            if self.current_uses < self.max_simultaneous_uses:  # Verifica se há espaço
                self.current_uses += 1
                print(f"{processo.name} iniciou E/S no dispositivo {self.id}. ({self.current_uses}/{self.max_simultaneous_uses} em uso)")
                threading.Thread(target=self._run_operation, args=(processo,)).start()
            else:
                print(f"{processo.name} entrou na fila de espera do dispositivo {self.id}.")
                self.queue.put(processo)  # Coloca o processo na fila de espera

    def _run_operation(self, processo):
        time.sleep(self.time_operation)  # Simula tempo de operação do dispositivo
        print(f"{processo.name} finalizou E/S no dispositivo {self.id}.")
        processo.state = "ready"  # Marca o processo como pronto após E/S
        with self.lock:
            self.current_uses -= 1  # Libera uma "vaga" no dispositivo
            if not self.queue.empty():
                next_process = self.queue.get()
                self.start_operation(next_process)  # Atende o próximo processo na fila, se houver
        
def check_states(processos, finalizados = []):
    prontos = []
    n = len(processos)
    for i in range(n):
        if processos[i].time_exec <= 0:
            finalizados.append(processos[i])
        elif processos[i].time_exec > 0:
            prontos.append(processos[i])
        else:
            print("ERRO NO MÓDULO:      check_states")
            
    return prontos, finalizados
        

def sorteio_requisicao(processo,devices,num_dispositivos):
    chance = random.random()   #Gerando um numero aleatorio entre 0 e 1
    if chance <= processo.chance_to_request/100:
        print("Requisição de E/S realizada.\n")
        num_sorted_device = random.randint(0,int(num_dispositivos)-1)
        sorted_device = "device-"+str(num_sorted_device)
        print(f"Dispositivo sorteado: ==={sorted_device}===")
        for device in devices:
            if device.id == sorted_device:
                if device.processes_using < device.simultaneous_uses:
                    device.processes_using += 1
                    processo.state = "blocked"
                    device.realiza_es()
                    print(f"{processo.name} começou a realizar uma operação de entrada e saída no dispositivo {device.id}...\n")
                    break
                else:
                    device.queue.append(processo)
                    processo.state = "blocked"
                    print(f"Processo {processo.name} entrou na fila de espera do dispositivo {device.id} ...\n")      
        return True
    else:
        print("Requisição não realizada\n")
        return False

def round_robin(processos,quantum,devices,num_dispositivos):
    
    quantum = int(quantum)
    sys.stdout.write("\nInicio do escalonamento\n###################\n")
    
    global prontos,finalizados
    prontos, finalizados = check_states(processos)
    
    tam_processos = len(processos)
    while True:
        sys.stdout.write("Quantidade de processos: {}\n".format(len(prontos)))
        sys.stdout.write("####### CPU #######\n")
        for proc in prontos:
            if proc.state != "blocked":
                if sorteio_requisicao(proc,devices,num_dispositivos):                #Confere se a requisicao de E/S será feita ou não        
                    continue
                else:
                    sys.stdout.write("\n## Processo: {}\n".format(proc.name))
                    sys.stdout.write("Tempo antes de processar: {}\n".format(proc.time_exec))
                    sys.stdout.write("Processando...\n")
                    
                    proc.processa(quantum)
                    
                    sys.stdout.write("Tempo restante: {}\n".format(proc.time_exec))
            else:
                continue
        
        prontos, finalizados = check_states(processos=prontos,finalizados=finalizados)
        sys.stdout.write("Processos finalizados: {}\n".format(len(finalizados)))
        if len(finalizados) == tam_processos:
            sys.stdout.write("\n####### FIM DO ESCALONAMENTO #######\nTodos os processos finalizados")
            break


def process_header_config(filename):
    # Abre o arquivo com os processos .
    with open(filename) as file_object:
        # Le o cabecalho do arquivo
        header = file_object.readline()
        escalonador, quantum,politica_mem,tam_memoria,tam_molduras,tam_aloc,acessos_ciclo,num_dispositivos = header.split("|")
        # Le o resto do arquivo com os processos
        file = file_object.readlines()      
        
        return header,escalonador, quantum,politica_mem,tam_memoria,tam_molduras,tam_aloc,acessos_ciclo,num_dispositivos,file
    
def process_global_config(line):
    parts = line.split('|')
    nomeProcesso = parts[0]
    PID = int(parts[1])
    tempoDeExecucao = int(parts[2])
    prioridade = int(parts[3])
    qtdeMemoria = int(parts[4])
    page_refs = list(map(int, parts[5].split()))  # Sequência de referências de página
    chance_request = int(parts[6])
    return Processo(nomeProcesso, PID, tempoDeExecucao, prioridade, qtdeMemoria, page_refs,chance_request)

def process_devices_config(line):
    parts = line.split('|')
    id = parts[0]
    sim_uses = parts[1]
    time_operation = parts[2]
    
    return Device(id,sim_uses,time_operation)
    

def main():
    
    diretorio_processos = ''
    arquivo = 'entrada_ES.txt'
    filename = diretorio_processos + arquivo

    # Processa a configuração global (primeira linha)
    header,escalonador, quantum,politica_mem,tam_memoria,tam_molduras,tam_aloc,acessos_ciclo,num_dispositivos,file = process_header_config(filename)
    
    print("Cabecalho do arquivo: {0}\nEscalonador: {1}\nQuantum: {2}\nPolitica de memoria: {3}\nTamanho Da Memoria: {4}\nTamanho das molduras: {5}\nTamanho das alocacoes: {6}\nAcessos por ciclo: {7}\nNumero de dispositivos: {8}\n".format(header, escalonador, quantum,politica_mem,tam_memoria,tam_molduras,tam_aloc,acessos_ciclo,num_dispositivos))
    
    i = int(num_dispositivos)
    devices = []
    processes = []

    #criando os devices
    for j in range(i):
        devices.append(process_devices_config(file[0]))
        del file[0]
    
    #criando os processos
    for n in range(len(file)):
        processes.append(process_global_config(file[n]))
    
    
    
    round_robin(processes,quantum,devices,num_dispositivos)
        
    #for i in range(len(file)):
        
        #processes.append(Processo(file[i]))
    
        
    
    
if __name__ == "__main__":
    main()