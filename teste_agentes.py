from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import random
import os

CARGOBOT_BASE_URL = "https://i4ds.github.io/CargoBot/"
# --- SELETORES ---
SELETOR_START_THE_GAME = "#click2start" 
SELETOR_PACOTE_EASY = "#pack_easy p" 
SELETOR_NIVEL_ALVO = "#level_0" 
SELETOR_CMD_BAIXO = "#tool_grab"    
SELETOR_CMD_DIREITA = "#tool_right"
SELETOR_CMD_ESQUERDA = "#tool_left"
SELETOR_CMD_F1_PALETA = "#tool_prog1" 
SELETOR_CMD_F2_PALETA = "#tool_prog2" 
SELETOR_CMD_F3_PALETA = "#tool_prog3"
SELETOR_CMD_F4_PALETA = "#tool_prog4" 
F1_SLOTS = [f"#reg_1_{i}" for i in range(8)] 
F2_SLOTS = [f"#reg_2_{i}" for i in range(8)] 
F3_SLOTS = [f"#reg_3_{i}" for i in range(8)]
F4_SLOTS = [f"#reg_4_{i}" for i in range(5)] 
SELETOR_BTN_PLAY_JOGO = "#play"
SELETOR_BTN_CLEAR_JOGO = "#btn_clear"
MODAL_CLEAR_CONFIRM_SELECTOR = "p#custom_modal_btn_clear_text:text('CLEAR')"

COMANDOS_BASICOS_PALETA = [
    (SELETOR_CMD_BAIXO, "Baixo"), (SELETOR_CMD_DIREITA, "Direita"), (SELETOR_CMD_ESQUERDA, "Esquerda")
]
COMANDOS_FUNCAO_PALETA = [
    (SELETOR_CMD_F1_PALETA, "Chamar F1"), (SELETOR_CMD_F2_PALETA, "Chamar F2"),
    (SELETOR_CMD_F3_PALETA, "Chamar F3"), (SELETOR_CMD_F4_PALETA, "Chamar F4")
]
TODOS_COMANDOS_TOOLBOX = COMANDOS_BASICOS_PALETA + COMANDOS_FUNCAO_PALETA # Todos os ícones da toolbox que podemos arrastar

# Classe Base do Agente (como antes, com __init__ corrigido)
class BaseAgent:
    def __init__(self, page, nome_agente, slow_mo_factor=1.0, max_tentativas=3, log_folder="agent_default_logs"):
        self.page = page
        self.nome_agente = nome_agente.replace(" ", "_") 
        self.slow_mo_factor = slow_mo_factor
        self.max_tentativas = max_tentativas
        self.tentativa_atual = 0
        self.log_acoes = []
        self.metricas_gerais = {
            "nome_agente": self.nome_agente, "tempo_total_inicio": time.time(),
            "tempo_total_fim": None, "duracao_total_s": None,
            "nivel_resolvido_final": False, "total_tentativas_feitas": 0,
            "total_cliques_play": 0, "total_usos_clear": 0,
            "total_comandos_colocados": 0, "erros_de_script": 0
        }
        self.agent_specific_log_folder = log_folder
        self.log_file_path = os.path.join(self.agent_specific_log_folder, f"log_{self.nome_agente}.txt")
        with open(self.log_file_path, "w", encoding="utf-8") as f:
            f.write(f"--- INÍCIO DO LOG PARA AGENTE: {self.nome_agente} ---\n")
        self._resetar_metricas_tentativa()

    def _resetar_metricas_tentativa(self):
        self.metricas_tentativa = {
            "comandos_colocados_nesta_tentativa": 0, "cliques_play_nesta_tentativa": 0,
            "programa_f1": [None]*len(F1_SLOTS), "programa_f2": [None]*len(F2_SLOTS),
            "programa_f3": [None]*len(F3_SLOTS), "programa_f4": [None]*len(F4_SLOTS),
        }

    def _log(self, acao, tipo="INFO"):
        timestamp_total = time.time() - self.metricas_gerais["tempo_total_inicio"]
        entrada_log = f"{timestamp_total:.2f}s [{tipo}] - {self.nome_agente} (Tentativa {self.tentativa_atual}): {acao}"
        print(entrada_log)
        self.log_acoes.append(entrada_log)
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(entrada_log + "\n")
        except Exception as e_log_write: print(f"!!! ERRO AO ESCREVER LOG {self.log_file_path}: {e_log_write}")

    def _pensar(self, segundos_base=1):
        time.sleep(segundos_base * self.slow_mo_factor * random.uniform(0.7, 1.3))

    def arrastar_para_slot(self, seletor_comando_paleta, seletor_slot_destino, nome_comando_log="Comando", func_slot_info=None):
        self._log(f"Tentando arrastar '{nome_comando_log}' ({seletor_comando_paleta}) para slot '{seletor_slot_destino}'")
        try:
            comando_a_arrastar = self.page.locator(seletor_comando_paleta)
            slot_alvo = self.page.locator(seletor_slot_destino)
            comando_a_arrastar.wait_for(timeout=5000, state="visible")
            slot_alvo.wait_for(timeout=5000, state="visible")
            comando_a_arrastar.drag_to(slot_alvo, timeout=5000)
            self.metricas_gerais["total_comandos_colocados"] += 1
            self.metricas_tentativa["comandos_colocados_nesta_tentativa"] += 1
            if func_slot_info:
                func_name_key, slot_idx, cmd_real = func_slot_info
                if func_name_key in self.metricas_tentativa and slot_idx < len(self.metricas_tentativa[func_name_key]):
                    self.metricas_tentativa[func_name_key][slot_idx] = cmd_real
            self._log(f"SUCESSO: '{nome_comando_log}' arrastado para '{seletor_slot_destino}'.")
        except Exception as e:
            self._log(f"ERRO AO ARRASTAR '{nome_comando_log}' para '{seletor_slot_destino}': {e}", tipo="SCRIPT_ERROR")
            self.metricas_gerais["erros_de_script"] += 1
            raise 
        self._pensar(0.1 * self.slow_mo_factor)

    def clicar_play_jogo(self):
        self._log("Clicando no Play do Jogo...")
        self.page.locator(SELETOR_BTN_PLAY_JOGO).click(timeout=5000)
        self.metricas_gerais["total_cliques_play"] += 1
        self.metricas_tentativa["cliques_play_nesta_tentativa"] += 1
        self._log("Play do Jogo clicado.")

    def clicar_clear_jogo(self):
        self._log("Clicando no Clear do Jogo...")
        try:
            self.page.locator(SELETOR_BTN_CLEAR_JOGO).click(timeout=7000)
            self._log("Botão Clear principal clicado.")
            self.page.locator(MODAL_CLEAR_CONFIRM_SELECTOR).click(timeout=3000) 
            self._log("Confirmado 'CLEAR' no modal.")
        except PlaywrightTimeoutError: self._log("Modal de confirmação Clear não apareceu (OK).")
        except Exception as e_clear: self._log(f"Aviso: Problema ao clicar/confirmar clear: {e_clear}", tipo="SCRIPT_WARNING")
        self.metricas_gerais["total_usos_clear"] += 1
        self._resetar_metricas_tentativa() 
        self._pensar(0.3)

    def navegar_para_nivel(self):
        self._log(f"Navegando para o nível {SELETOR_NIVEL_ALVO}...")
        self.page.goto(CARGOBOT_BASE_URL, timeout=60000, wait_until="domcontentloaded") 
        self._pensar(1.5)
        self.page.locator(SELETOR_START_THE_GAME).click(timeout=15000); self._pensar(0.3)
        self.page.locator(SELETOR_PACOTE_EASY).click(timeout=15000); self._pensar(0.3)  
        self.page.locator(SELETOR_NIVEL_ALVO).click(timeout=15000)
        self._log(f"Navegação para '{SELETOR_NIVEL_ALVO}' completa. URL: {self.page.url}") 
        self._pensar(2.5) 

    def _verificar_sucesso_nivel(self, tempo_execucao_jogo=5): 
        self._log(f"Observando execução do jogo por {tempo_execucao_jogo}s para verificar sucesso...")
        self._pensar(tempo_execucao_jogo) 
        try:
            self.page.locator("text=/YOU GOT IT/i").wait_for(timeout=1000, state="visible") 
            self._log("Tela 'YOU GOT IT' detectada!", tipo="SUCESSO_NIVEL")
            return True
        except PlaywrightTimeoutError:
            self._log("Tela 'YOU GOT IT' não detectada.", tipo="FALHA_NIVEL")
            return False

    def finalizar_sessao_agente(self):
        self.metricas_gerais["tempo_total_fim"] = time.time()
        duracao = self.metricas_gerais["tempo_total_fim"] - self.metricas_gerais["tempo_total_inicio"]
        self.metricas_gerais["duracao_total_s"] = round(duracao, 2)
        self.metricas_gerais["total_tentativas_feitas"] = self.tentativa_atual
        log_final_sessao = f"SESSÃO DO AGENTE FINALIZADA. Resolvido: {self.metricas_gerais['nivel_resolvido_final']}. Tentativas: {self.metricas_gerais['total_tentativas_feitas']}. Duração: {self.metricas_gerais['duracao_total_s']}s"
        self._log(log_final_sessao, tipo="FINAL_SESSAO")
        with open(self.log_file_path, "a", encoding="utf-8") as f:
            f.write("\n--- MÉTRICAS FINAIS ---\n")
            for chave, valor in self.metricas_gerais.items(): f.write(f"  {chave}: {valor}\n")
            f.write("--- FIM DAS MÉTRICAS ---\n")

    def run(self):
        self.tentativa_atual = 0
        try: # Try-except para a navegação, caso ela falhe.
            self.navegar_para_nivel()
            self.clicar_clear_jogo() 
        except Exception as e_nav:
            self._log(f"ERRO FATAL DURANTE NAVEGAÇÃO OU CLEAR INICIAL: {e_nav}", tipo="FATAL_ERROR")
            self.metricas_gerais["erros_de_script"] +=1
            self.finalizar_sessao_agente()
            return # Não prossegue se a navegação falhar

        while self.tentativa_atual < self.max_tentativas:
            self.tentativa_atual += 1
            self._log(f"Iniciando tentativa {self.tentativa_atual}/{self.max_tentativas}")
            try:
                resolvido_nesta_tentativa = self.logica_da_persona_para_tentativa()
                if resolvido_nesta_tentativa:
                    self.metricas_gerais["nivel_resolvido_final"] = True; break 
                elif self.tentativa_atual < self.max_tentativas:
                    self._log("Não resolveu. Limpando para a próxima tentativa.")
                    self.clicar_clear_jogo() 
                else: self._log("Máximo de tentativas alcançado sem resolver.")
            except PlaywrightTimeoutError as pte: 
                 self._log(f"ERRO DE TIMEOUT DO PLAYWRIGHT NA TENTATIVA: {pte}", tipo="SCRIPT_ERROR")
                 self.metricas_gerais["erros_de_script"] += 1
                 if self.tentativa_atual < self.max_tentativas: self.clicar_clear_jogo()
            except Exception as e_script: 
                self._log(f"ERRO DE SCRIPT INESPERADO NA TENTATIVA: {e_script}", tipo="SCRIPT_ERROR")
                self.metricas_gerais["erros_de_script"] += 1
                if self.tentativa_atual < self.max_tentativas: self.clicar_clear_jogo()
            if self.metricas_gerais["nivel_resolvido_final"]: break
        self.finalizar_sessao_agente()

    def logica_da_persona_para_tentativa(self):
        raise NotImplementedError("Persona deve implementar 'logica_da_persona_para_tentativa'")

# --- PERSONAS ---

class AgenteSolucionadorPerfeito(BaseAgent):
    def __init__(self, page, log_folder):
        super().__init__(page, "Aluno_Perfeito_SolucaoImagem", slow_mo_factor=0.3, max_tentativas=1, log_folder=log_folder)
    def logica_da_persona_para_tentativa(self): # Implementa a solução humana 
        self._log("Aplicando solução da imagem (F1->F2->F4->F3)...")
        try:
            # F1
            cmd_f1 = [(SELETOR_CMD_BAIXO, "B"), (SELETOR_CMD_DIREITA, "D"), (SELETOR_CMD_BAIXO, "B"), (SELETOR_CMD_ESQUERDA, "E"), (SELETOR_CMD_BAIXO, "B"), (SELETOR_CMD_DIREITA, "D"), (SELETOR_CMD_BAIXO, "B"), (SELETOR_CMD_F2_PALETA, "F2")]
            for i, (cs,cn) in enumerate(cmd_f1): self.arrastar_para_slot(cs, F1_SLOTS[i], cn, ("programa_f1",i,cn))
            # F2 (Chama F4)
            cmd_f2 = [(SELETOR_CMD_ESQUERDA, "E"), (SELETOR_CMD_BAIXO, "B"), (SELETOR_CMD_DIREITA, "D"), (SELETOR_CMD_BAIXO, "B"), (SELETOR_CMD_ESQUERDA, "E"), (SELETOR_CMD_BAIXO, "B"), (SELETOR_CMD_DIREITA, "D"), (SELETOR_CMD_F4_PALETA, "F4")]
            for i, (cs,cn) in enumerate(cmd_f2): self.arrastar_para_slot(cs, F2_SLOTS[i], cn, ("programa_f2",i,cn))
            # F3 (Chama F1)
            cmd_f3 = [(SELETOR_CMD_DIREITA, "D"), (SELETOR_CMD_BAIXO, "B"),(SELETOR_CMD_ESQUERDA, "E"), (SELETOR_CMD_BAIXO, "B"),(SELETOR_CMD_DIREITA, "D"), (SELETOR_CMD_BAIXO, "B"),(SELETOR_CMD_ESQUERDA, "E"), (SELETOR_CMD_F1_PALETA, "F1")]
            for i, (cs,cn) in enumerate(cmd_f3): self.arrastar_para_slot(cs, F3_SLOTS[i], cn, ("programa_f3",i,cn))
            # F4 (Chama F3)
            cmd_f4 = [(SELETOR_CMD_DIREITA, "D"), (SELETOR_CMD_BAIXO, "B"), (SELETOR_CMD_ESQUERDA, "E"), (SELETOR_CMD_BAIXO, "B"), (SELETOR_CMD_F3_PALETA, "F3")]
            for i, (cs,cn) in enumerate(cmd_f4): self.arrastar_para_slot(cs, F4_SLOTS[i], cn, ("programa_f4",i,cn))
            self.clicar_play_jogo()
            return self._verificar_sucesso_nivel(tempo_execucao_jogo=60) 
        except Exception as e: self._log(f"Erro: {e}", "AGENT_ERROR"); return False

class AgenteInicianteExplorador(BaseAgent): # Cauteloso
    def __init__(self, page, log_folder):
        super().__init__(page, "Aluno_Iniciante_Explorador", slow_mo_factor=1.8, max_tentativas=2, log_folder=log_folder)
    def logica_da_persona_para_tentativa(self): # Tenta um ou dois comandos em F1 e testa
        self._log(f"Explorador: Tentativa {self.tentativa_atual}")
        try:
            num_cmds_to_try = 1 if self.tentativa_atual == 1 else 2
            for i in range(num_cmds_to_try):
                cmd_s, cmd_n = random.choice(COMANDOS_BASICOS_PALETA)
                self.arrastar_para_slot(cmd_s, F1_SLOTS[i], cmd_n, ("programa_f1",i,cmd_n))
                self._pensar(1) # Pensa entre cada comando
            if self.metricas_tentativa["comandos_colocados_nesta_tentativa"] > 0:
                self.clicar_play_jogo()
                return self._verificar_sucesso_nivel(tempo_execucao_jogo=7)
            return False
        except Exception as e: self._log(f"Erro: {e}", "AGENT_ERROR"); return False

class AgenteImpulsivoAleatorio(BaseAgent): # Tentativa e erro rápida
    def __init__(self, page, log_folder):
        super().__init__(page, "Aluno_Impulsivo_Aleatorio", slow_mo_factor=0.7, max_tentativas=4, log_folder=log_folder)
    def logica_da_persona_para_tentativa(self): # Preenche F1 aleatoriamente, talvez F2
        self._log(f"Impulsivo: Tentativa {self.tentativa_atual}")
        try:
            for i in range(random.randint(4, len(F1_SLOTS))): # Preenche boa parte de F1
                if random.random() < 0.15 and i == len(F1_SLOTS) -1 : # Pequena chance de chamar F2
                    cmd_s, cmd_n = SELETOR_CMD_F2_PALETA, "Chamar F2"
                    self.arrastar_para_slot(cmd_s, F1_SLOTS[i], cmd_n, ("programa_f1",i,cmd_n))
                    for j in range(random.randint(1,3)): # Alguns comandos em F2
                        cmd_s2, cmd_n2 = random.choice(COMANDOS_BASICOS_PALETA)
                        self.arrastar_para_slot(cmd_s2, F2_SLOTS[j], cmd_n2, ("programa_f2",j,cmd_n2))
                else:
                    cmd_s, cmd_n = random.choice(COMANDOS_BASICOS_PALETA)
                    self.arrastar_para_slot(cmd_s, F1_SLOTS[i], cmd_n, ("programa_f1",i,cmd_n))
            if self.metricas_tentativa["comandos_colocados_nesta_tentativa"] > 0:
                self.clicar_play_jogo()
            return self._verificar_sucesso_nivel(tempo_execucao_jogo=15)
        except Exception as e: self._log(f"Erro: {e}", "AGENT_ERROR"); return False

class AgenteMetodicoF1(BaseAgent): # Tenta tudo em F1
    def __init__(self, page, log_folder):
        super().__init__(page, "Aluno_Metodico_F1", slow_mo_factor=1.2, max_tentativas=2, log_folder=log_folder)
    def logica_da_persona_para_tentativa(self):
        self._log(f"Metódico F1: Tentativa {self.tentativa_atual}")
        # Tenta construir uma solução mais longa apenas em F1
        # (Lógica de exemplo: tenta mover 3 blocos de C1 para C3, um por vez, usando C2 como temp)
        # Esta lógica é para o Double Flip CLÁSSICO de 3 blocos, só para exemplo de comportamento.
        # Não vai resolver o nível atual de 4 blocos.
        try:
            # Mover 1º bloco (topo de C1) para C2
            self.arrastar_para_slot(SELETOR_CMD_BAIXO, F1_SLOTS[0], "Pega1",("programa_f1",0,"Pega1"))
            self.arrastar_para_slot(SELETOR_CMD_DIREITA, F1_SLOTS[1], "Dir1",("programa_f1",1,"Dir1"))
            self.arrastar_para_slot(SELETOR_CMD_BAIXO, F1_SLOTS[2], "Larga1",("programa_f1",2,"Larga1"))
            if self.tentativa_atual == 1: # Na primeira tentativa, testa só isso
                self.clicar_play_jogo()
                if self._verificar_sucesso_nivel(5) : return True
                self.clicar_clear_jogo() # Limpa para a próxima etapa da sua lógica
                # Precisa arrastar novamente se limpou
                self.arrastar_para_slot(SELETOR_CMD_BAIXO, F1_SLOTS[0], "Pega1",("programa_f1",0,"Pega1"))
                self.arrastar_para_slot(SELETOR_CMD_DIREITA, F1_SLOTS[1], "Dir1",("programa_f1",1,"Dir1"))
                self.arrastar_para_slot(SELETOR_CMD_BAIXO, F1_SLOTS[2], "Larga1",("programa_f1",2,"Larga1"))

            # Mover 2º bloco (meio de C1) para C3
            self.arrastar_para_slot(SELETOR_CMD_ESQUERDA, F1_SLOTS[3], "Esq1",("programa_f1",3,"Esq1"))
            self.arrastar_para_slot(SELETOR_CMD_BAIXO, F1_SLOTS[4], "Pega2",("programa_f1",4,"Pega2"))
            self.arrastar_para_slot(SELETOR_CMD_DIREITA, F1_SLOTS[5], "Dir2",("programa_f1",5,"Dir2"))
            self.arrastar_para_slot(SELETOR_CMD_DIREITA, F1_SLOTS[6], "Dir3",("programa_f1",6,"Dir3"))
            self.arrastar_para_slot(SELETOR_CMD_BAIXO, F1_SLOTS[7], "Larga2",("programa_f1",7,"Larga2"))
            
            self.clicar_play_jogo()
            return self._verificar_sucesso_nivel(tempo_execucao_jogo=20)
        except Exception as e: self._log(f"Erro: {e}", "AGENT_ERROR"); return False

class AgenteConfusoComChamadas(BaseAgent):
    def __init__(self, page, log_folder):
        super().__init__(page, "Aluno_Confuso_Chamadas", slow_mo_factor=1.5, max_tentativas=2, log_folder=log_folder)
    def logica_da_persona_para_tentativa(self):
        self._log(f"Confuso Chamadas: Tentativa {self.tentativa_atual}")
        # Tenta usar F1 e F2, mas pode errar a chamada
        try:
            # F1 - alguns comandos
            for i in range(random.randint(2,4)):
                cmd_s, cmd_n = random.choice(COMANDOS_BASICOS_PALETA)
                self.arrastar_para_slot(cmd_s, F1_SLOTS[i], cmd_n, ("programa_f1",i,cmd_n))
            
            # F2 - alguns comandos
            for i in range(random.randint(2,4)):
                cmd_s, cmd_n = random.choice(COMANDOS_BASICOS_PALETA)
                self.arrastar_para_slot(cmd_s, F2_SLOTS[i], cmd_n, ("programa_f2",i,cmd_n))

            # Erro na chamada:
            if random.random() < 0.4: # Esquece de chamar F2
                self._log("Confuso: Esqueci de chamar F2 de F1.")
            elif random.random() < 0.7: # Chama F2 no meio de F1
                slot_errado_f1 = random.randint(0,3)
                self._log(f"Confuso: Chamando F2 do slot {slot_errado_f1} de F1.")
                self.arrastar_para_slot(SELETOR_CMD_F2_PALETA, F1_SLOTS[slot_errado_f1], "Chamar F2",("programa_f1",slot_errado_f1,"Chamar F2"))
            else: # Chama F2 corretamente no final de F1
                self.arrastar_para_slot(SELETOR_CMD_F2_PALETA, F1_SLOTS[7], "Chamar F2",("programa_f1",7,"Chamar F2"))
            
            self.clicar_play_jogo()
            return self._verificar_sucesso_nivel(tempo_execucao_jogo=15)
        except Exception as e: self._log(f"Erro: {e}", "AGENT_ERROR"); return False

class AgenteSuperOtimista(BaseAgent):
    def __init__(self, page, log_folder):
        super().__init__(page, "Aluno_Super_Otimista", slow_mo_factor=0.5, max_tentativas=1, log_folder=log_folder)
    def logica_da_persona_para_tentativa(self):
        self._log("Super Otimista: Vou tentar em 3 passos!")
        # Tenta uma solução muito curta que provavelmente falha
        try:
            self.arrastar_para_slot(SELETOR_CMD_BAIXO, F1_SLOTS[0], "Pega",("programa_f1",0,"Pega"))
            self.arrastar_para_slot(SELETOR_CMD_DIREITA, F1_SLOTS[1], "Direita",("programa_f1",1,"Direita"))
            self.arrastar_para_slot(SELETOR_CMD_DIREITA, F1_SLOTS[2], "Direita",("programa_f1",2,"Direita"))
            self.arrastar_para_slot(SELETOR_CMD_BAIXO, F1_SLOTS[3], "Larga",("programa_f1",3,"Larga")) # 4 passos na verdade
            self.clicar_play_jogo()
            return self._verificar_sucesso_nivel(tempo_execucao_jogo=8)
        except Exception as e: self._log(f"Erro: {e}", "AGENT_ERROR"); return False

# --- FUNÇÃO PRINCIPAL PARA RODAR OS TESTES ---
def rodar_agentes_para_usabilidade(lista_de_agentes_classes):
    all_results_summary = []
    log_folder_base = "agent_run_logs" 
    if not os.path.exists(log_folder_base): os.makedirs(log_folder_base)
    execution_timestamp = time.strftime("%Y%m%d-%H%M%S")
    current_execution_log_folder = os.path.join(log_folder_base, execution_timestamp)
    if not os.path.exists(current_execution_log_folder): os.makedirs(current_execution_log_folder)
    print(f"Logs desta execução serão salvos em: {current_execution_log_folder}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100) 
        for i, AgenteClasse in enumerate(lista_de_agentes_classes):
            print(f"\n\n--- INICIANDO TESTE COM AGENTE TIPO: {AgenteClasse.__name__} ---")
            page = browser.new_page()
            agente = AgenteClasse(page, log_folder=current_execution_log_folder) 
            agente.run() 
            all_results_summary.append(agente.metricas_gerais) 
            print(f"--- TESTE COM AGENTE {AgenteClasse.__name__} CONCLUÍDO ---")
            page.close() 
            if i < len(lista_de_agentes_classes) - 1:
                print("Pausa de 3s antes do próximo agente...")
                time.sleep(3)
        browser.close() 
    print("\n\n--- TODOS OS TESTES DE USABILIDADE SIMULADOS CONCLUÍDOS ---")
    print(f"Logs detalhados de cada agente foram salvos na pasta: {current_execution_log_folder}")
    print("\n--- RESUMO DAS MÉTRICAS GERAIS POR AGENTE ---")
    for resultado_agente in all_results_summary:
        print(f"\nAgente: {resultado_agente['nome_agente']}")
        for chave, valor in resultado_agente.items():
            if chave not in ["nome_agente", "tempo_total_inicio", "tempo_total_fim"]: 
                 print(f"  {chave}: {valor}")

if __name__ == "__main__":
    agentes_a_testar = [
        AgenteSolucionadorPerfeito,     
        AgenteInicianteExplorador,
        AgenteImpulsivoAleatorio,
        AgenteMetodicoF1,
        AgenteConfusoComChamadas,
        AgenteSuperOtimista,
    ]
    rodar_agentes_para_usabilidade(agentes_a_testar)