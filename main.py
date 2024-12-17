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
from queue import Queue

class Processo:
    def __init__(self, name, PID, time_exec, prioridade, qnt_memoria, pages_sequence, chance_to_request):
        self.name = name
        self.PID = int(PID)
        self.time_exec = int(time_exec)
        self.prioridade = int(prioridade)
        self.qnt_memoria = int(qnt_memoria)
        self.pages_sequence = [pages_sequence]
        self.chance_to_request = int(chance_to_request)
        self.time_processed = 0
        self.state = "ready"

    def processa(self, quantum):
        for i in tqdm(range(quantum)):
            time.sleep(0.5)
        self.time_processed += quantum
        self.time_exec -= quantum

class Device:
    def __init__(self, id, sim_uses, time_operation):
        self.id = str(id)
        self.simultaneous_uses = int(sim_uses)
        self.time_operation = int(time_operation)
        self.current_uses = 0
        self.queue = Queue()
        self.lock = threading.Lock()

    def start_operation(self, processo):
        with self.lock:
            if self.current_uses < self.simultaneous_uses:
                self.current_uses += 1
                print(f"{processo.name} iniciou E/S no dispositivo {self.id} ({self.current_uses}/{self.simultaneous_uses} em uso)")
                threading.Thread(target=self._run_operation, args=(processo,)).start()
            else:
                print(f"{processo.name} entrou na fila de espera do dispositivo {self.id}")
                self.queue.put(processo)

    def _run_operation(self, processo):
        time.sleep(self.time_operation)
        print(f"{processo.name} finalizou E/S no dispositivo {self.id}")
        processo.state = "ready"
        with self.lock:
            self.current_uses -= 1
            if not self.queue.empty():
                next_process = self.queue.get()
                self.start_operation(next_process)

def check_states(processos, finalizados=[]):
    prontos = []
    for processo in processos:
        if processo.time_exec <= 0:
            finalizados.append(processo)
        else:
            prontos.append(processo)
    return prontos, finalizados

def sorteio_requisicao(processo, devices, num_dispositivos):
    chance = random.random()
    if chance <= processo.chance_to_request / 100:
        num_sorted_device = random.randint(0, int(num_dispositivos) - 1)
        sorted_device = devices[num_sorted_device]
        processo.state = "blocked"
        sorted_device.start_operation(processo)
        return True
    return False

def round_robin(processos, quantum, devices, num_dispositivos):
    prontos, finalizados = check_states(processos)
    tam_processos = len(processos)
    while True:
        for proc in prontos:
            if proc.state == "ready":
                if sorteio_requisicao(proc, devices, num_dispositivos):
                    continue
                print(f"\n## Processo: {proc.name}")
                print(f"Tempo antes de processar: {proc.time_exec}")
                proc.processa(quantum)
                print(f"Tempo restante: {proc.time_exec}")
        prontos, finalizados = check_states(prontos, finalizados)
        if len(finalizados) == tam_processos:
            print("\n####### FIM DO ESCALONAMENTO #######\nTodos os processos finalizados")
            break

def process_header_config(filename):
    with open(filename) as file_object:
        header = file_object.readline()
        escalonador, quantum, politica_mem, tam_memoria, tam_molduras, tam_aloc, acessos_ciclo, num_dispositivos = header.split("|")
        file = file_object.readlines()
        return header, escalonador, quantum, politica_mem, tam_memoria, tam_molduras, tam_aloc, acessos_ciclo, num_dispositivos, file

def process_global_config(line):
    parts = line.split('|')
    nomeProcesso = parts[0]
    PID = int(parts[1])
    tempoDeExecucao = int(parts[2])
    prioridade = int(parts[3])
    qtdeMemoria = int(parts[4])
    page_refs = list(map(int, parts[5].split()))
    chance_request = int(parts[6])
    return Processo(nomeProcesso, PID, tempoDeExecucao, prioridade, qtdeMemoria, page_refs, chance_request)

def process_devices_config(line):
    parts = line.split('|')
    id = parts[0]
    sim_uses = parts[1]
    time_operation = parts[2]
    return Device(id, sim_uses, time_operation)

def main():
    diretorio_processos = ''
    arquivo = 'entrada_ES.txt'
    filename = diretorio_processos + arquivo

    header, escalonador, quantum, politica_mem, tam_memoria, tam_molduras, tam_aloc, acessos_ciclo, num_dispositivos, file = process_header_config(filename)

    devices = [process_devices_config(file[i]) for i in range(int(num_dispositivos))]
    processes = [process_global_config(line) for line in file[int(num_dispositivos):]]

    round_robin(processes, int(quantum), devices, int(num_dispositivos))

if __name__ == "__main__":
    main()
