import pygame
import math
import random 
import json
import os
from collections import deque

C_BG_DARK     = (20, 23, 30) 
C_BG_GRID     = (35, 40, 50)
C_NODE_OFF    = (60, 70, 80)
C_NODE_BORDER = (100, 110, 130)
C_EDGE        = (50, 60, 70)

C_VISITADO    = (0, 200, 150)
C_FILA        = (255, 180, 0)
C_ATUAL       = (255, 50, 100)
C_ERROR       = (200, 50, 50)
C_GOLD        = (218, 165, 32)

C_TEXT_WHITE  = (240, 240, 245)
C_TEXT_GREY   = (150, 160, 170)
C_UI_PANEL    = (30, 35, 45, 200)
C_BTN_NORMAL  = (50, 60, 80)
C_BTN_HOVER   = (70, 80, 100)
C_BTN_ACTIVE  = (0, 180, 130)

LARGURA, ALTURA = 1000, 700
ARQUIVO_RECORDES = "recordes_graph_arcade.json"

DIFICULDADES = {
    "Noob":   {"camadas": 2, "ciclos": 0.0, "min_nos": 1, "max_nos": 2},
    "Fácil":  {"camadas": 3, "ciclos": 0.1, "min_nos": 2, "max_nos": 3},
    "Normal": {"camadas": 4, "ciclos": 0.3, "min_nos": 2, "max_nos": 4},
    "Pro":    {"camadas": 5, "ciclos": 0.5, "min_nos": 3, "max_nos": 5},
    "Hacker": {"camadas": 7, "ciclos": 0.8, "min_nos": 4, "max_nos": 6}
}

ESTADO_MENU = 0
ESTADO_JOGANDO = 1
ESTADO_INPUT_NOME = 2
ESTADO_RANKING = 3
ESTADO_DERROTA = 4

pygame.init()
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Neural Graph: Arcade Edition")

def get_font(size, bold=False):
    fonts = ['Segoe UI', 'Roboto', 'Helvetica', 'Arial']
    return pygame.font.SysFont(fonts, size, bold=bold)

fonte_ui = get_font(18)
fonte_bold = get_font(22, bold=True)
fonte_titulo = get_font(50, bold=True)
fonte_mini = get_font(14)

class Node:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.vizinhos = []
        self.visitado = False
        self.na_fila = False 
        self.hover = False

    def desenhar(self, tela, surface_glow):
        fill_color = C_NODE_OFF
        border_color = C_NODE_BORDER
        radius = 18
        
        if self.visitado:
            fill_color = C_VISITADO
            border_color = (200, 255, 230)
            pygame.draw.circle(surface_glow, (*C_VISITADO, 50), (self.x, self.y), 30)
        elif self.na_fila:
            fill_color = C_NODE_OFF
            border_color = C_FILA
            pygame.draw.circle(surface_glow, (*C_FILA, 30), (self.x, self.y), 25)

        if self.hover and not self.visitado:
            border_color = (255, 255, 255)
            radius = 20

        pygame.draw.circle(tela, fill_color, (self.x, self.y), radius)
        pygame.draw.circle(tela, border_color, (self.x, self.y), radius, 2)
        
        text_color = C_BG_DARK if self.visitado else C_TEXT_WHITE
        txt = fonte_bold.render(str(self.id), True, text_color)
        tela.blit(txt, (self.x - txt.get_width()//2, self.y - txt.get_height()//2))

class GraphGame:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.no_atual = None
        self.modo = "BFS"
        self.fila_esperada = deque() 
        self.gabarito = []
        
        self.estado = ESTADO_MENU
        self.energia_max = 100
        self.energia_atual = 100
        self.dificuldade_atual = "Normal"
        
        self.start_ticks = 0
        self.tempo_final = 0.0
        self.pontuacao_final = 0
        self.nome_jogador = ""
        self.recordes = self.carregar_recordes()

        self.botoes_menu = []
        self.botao_bfs = pygame.Rect(0,0,0,0)
        self.botao_dfs = pygame.Rect(0,0,0,0)
        self.botao_voltar_menu = pygame.Rect(0,0,0,0)

    def carregar_recordes(self):
        if not os.path.exists(ARQUIVO_RECORDES):
            return {}
        try:
            with open(ARQUIVO_RECORDES, 'r') as f:
                return json.load(f)
        except:
            return {}

    def salvar_recorde(self):
        chave = f"{self.modo}_{self.dificuldade_atual}"
        if chave not in self.recordes:
            self.recordes[chave] = []
        
        self.recordes[chave].append([self.nome_jogador, self.pontuacao_final, self.tempo_final])
        self.recordes[chave].sort(key=lambda x: x[1], reverse=True)
        self.recordes[chave] = self.recordes[chave][:5]
        
        with open(ARQUIVO_RECORDES, 'w') as f:
            json.dump(self.recordes, f)

    def add_edge(self, u, v):
        if self.nodes[v] not in self.nodes[u].vizinhos:
            self.nodes[u].vizinhos.append(self.nodes[v])
            self.nodes[v].vizinhos.append(self.nodes[u])
            self.edges.append((self.nodes[u], self.nodes[v]))

    def iniciar_nivel(self, nome_dificuldade):
        self.dificuldade_atual = nome_dificuldade
        config = DIFICULDADES[nome_dificuldade]
        self.gerar_fase(config)
        self.estado = ESTADO_JOGANDO
        self.start_ticks = pygame.time.get_ticks()

    def gerar_fase(self, config):
        self.nodes = {}
        self.edges = []
        self.gabarito = []
        self.energia_atual = self.energia_max
        
        num_camadas = config["camadas"]
        densidade_ciclos = config["ciclos"]
        min_nos = config["min_nos"]
        max_nos = config["max_nos"]

        margem_x = 80
        margem_y = 120
        altura_nivel = (ALTURA - margem_y - 80) // num_camadas

        id_counter = 0
        root = Node(id_counter, LARGURA // 2, margem_y)
        self.nodes[id_counter] = root
        camada_anterior = [root] 
        id_counter += 1

        for i in range(1, num_camadas + 1):
            y_base = margem_y + (i * altura_nivel)
            qtd_nos = random.randint(min_nos, max_nos)
            largura_setor = (LARGURA - 2 * margem_x) // qtd_nos
            camada_atual = []
            
            for j in range(qtd_nos):
                jitter = random.randint(-25, 25) 
                x_pos = margem_x + (j * largura_setor) + (largura_setor // 2) + jitter
                y_pos = y_base + random.randint(-15, 15)
                
                novo_no = Node(id_counter, x_pos, y_pos)
                self.nodes[id_counter] = novo_no
                camada_atual.append(novo_no)
                id_counter += 1
                
                pai = random.choice(camada_anterior)
                self.add_edge(pai.id, novo_no.id)

            chance_ciclo = densidade_ciclos
            if self.modo == "DFS": chance_ciclo *= 0.5 

            for no in camada_atual:
                if random.random() < chance_ciclo and id_counter > 5:
                    alvo_id = random.randint(0, id_counter - 2)
                    if alvo_id != no.id:
                        self.add_edge(no.id, alvo_id)

            camada_anterior = camada_atual 

        self.no_atual = self.nodes[0]
        self.no_atual.visitado = True
        self.recalcular_gabarito()

    def recalcular_gabarito(self):
        self.gabarito = []
        start_node = self.nodes[0]
        
        if self.modo == "BFS":
            fila = deque([start_node])
            visitados = {start_node.id}
            while fila:
                atual = fila.popleft()
                if atual.id != 0: self.gabarito.append(atual.id)
                vizinhos_ordenados = sorted(atual.vizinhos, key=lambda n: n.id)
                for vizinho in vizinhos_ordenados:
                    if vizinho.id not in visitados:
                        visitados.add(vizinho.id)
                        fila.append(vizinho)
        
        elif self.modo == "DFS":
            pilha = [start_node]
            visitados = set()
            while pilha:
                atual = pilha.pop()
                if atual.id not in visitados:
                    visitados.add(atual.id)
                    if atual.id != 0: self.gabarito.append(atual.id)
                    vizinhos_ordenados = sorted(atual.vizinhos, key=lambda n: n.id, reverse=True)
                    for vizinho in vizinhos_ordenados:
                        if vizinho.id not in visitados:
                            pilha.append(vizinho)

    def processar_clique(self, pos_mouse):
        if self.estado == ESTADO_MENU:
            if self.botao_bfs.collidepoint(pos_mouse):
                self.modo = "BFS"
            elif self.botao_dfs.collidepoint(pos_mouse):
                self.modo = "DFS"
            
            for nome, rect in self.botoes_menu:
                if rect.collidepoint(pos_mouse):
                    self.iniciar_nivel(nome)
            return
        
        if self.estado == ESTADO_RANKING:
            if self.botao_voltar_menu.collidepoint(pos_mouse):
                self.estado = ESTADO_MENU
            return

        if self.estado != ESTADO_JOGANDO:
            return

        for id, node in self.nodes.items():
            dist = math.hypot(pos_mouse[0] - node.x, pos_mouse[1] - node.y)
            if dist < 30:
                self.validar_movimento(node)
                break

    def validar_movimento(self, node_clicado):
        if node_clicado.visitado: return 
        if not self.gabarito: return

        proximo_correto_id = self.gabarito[0]
        
        if node_clicado.id == proximo_correto_id:
            node_clicado.visitado = True
            self.no_atual = node_clicado
            self.gabarito.pop(0)
            
            if not self.gabarito:
                self.tempo_final = (pygame.time.get_ticks() - self.start_ticks) / 1000
                bonus_energia = int(self.energia_atual * 100)
                bonus_tempo = int(max(0, 5000 - (self.tempo_final * 10)))
                self.pontuacao_final = bonus_energia + bonus_tempo
                self.nome_jogador = "" 
                self.estado = ESTADO_INPUT_NOME
        else:
            self.energia_atual -= 15
            if self.energia_atual <= 0:
                self.energia_atual = 0
                self.estado = ESTADO_DERROTA

    def processar_input_nome(self, evento):
        if evento.key == pygame.K_RETURN:
            if self.nome_jogador.strip() == "":
                self.nome_jogador = "Anonimo"
            self.salvar_recorde()
            self.estado = ESTADO_RANKING
        elif evento.key == pygame.K_BACKSPACE:
            self.nome_jogador = self.nome_jogador[:-1]
        else:
            if len(self.nome_jogador) < 12:
                self.nome_jogador += evento.unicode

    def update_hover(self, pos_mouse):
        if self.estado != ESTADO_JOGANDO: return
        for node in self.nodes.values():
            dist = math.hypot(pos_mouse[0] - node.x, pos_mouse[1] - node.y)
            node.hover = (dist < 25)

    def desenhar_background(self, tela):
        tamanho_grid = 40
        for x in range(0, LARGURA, tamanho_grid):
            pygame.draw.line(tela, C_BG_GRID, (x, 0), (x, ALTURA), 1)
        for y in range(0, ALTURA, tamanho_grid):
            pygame.draw.line(tela, C_BG_GRID, (0, y), (LARGURA, y), 1)

    def draw_button(self, tela, rect, text, active=False, hover=False, custom_color=None):
        cor_base = custom_color if custom_color else C_BTN_NORMAL
        cor_fundo = C_BTN_ACTIVE if active else (C_BTN_HOVER if hover else cor_base)
        cor_borda = (255, 255, 255) if hover else C_NODE_BORDER
        
        pygame.draw.rect(tela, cor_fundo, rect, border_radius=12)
        pygame.draw.rect(tela, cor_borda, rect, 2, border_radius=12)
        txt_surf = fonte_bold.render(text, True, C_TEXT_WHITE)
        tela.blit(txt_surf, (rect.centerx - txt_surf.get_width()//2, rect.centery - txt_surf.get_height()//2))

    def desenhar_menu(self, tela, pos_mouse):
        tit = "NEURAL GRAPH"
        sombra = fonte_titulo.render(tit, True, (0, 0, 0))
        texto = fonte_titulo.render(tit, True, C_VISITADO)
        tela.blit(sombra, (LARGURA//2 - texto.get_width()//2 + 4, 54))
        tela.blit(texto, (LARGURA//2 - texto.get_width()//2, 50))
        
        sub = fonte_ui.render("Arcade Edition: Score & Speed", True, C_TEXT_GREY)
        tela.blit(sub, (LARGURA//2 - sub.get_width()//2, 100))

        lbl_mode = fonte_bold.render("SELECIONE O PROTOCOLO:", True, C_TEXT_WHITE)
        tela.blit(lbl_mode, (LARGURA//2 - lbl_mode.get_width()//2, 160))

        bw, bh = 240, 50
        gap = 20
        start_x = LARGURA//2 - bw - gap//2
        self.botao_bfs = pygame.Rect(start_x, 200, bw, bh)
        self.botao_dfs = pygame.Rect(start_x + bw + gap, 200, bw, bh)

        self.draw_button(tela, self.botao_bfs, "BFS (Largura)", active=(self.modo=="BFS"), hover=self.botao_bfs.collidepoint(pos_mouse))
        self.draw_button(tela, self.botao_dfs, "DFS (Profund.)", active=(self.modo=="DFS"), hover=self.botao_dfs.collidepoint(pos_mouse))

        desc_txt = "Onda expandindo em camadas." if self.modo == "BFS" else "Caminho único até o fim."
        desc = fonte_mini.render(desc_txt, True, C_FILA)
        tela.blit(desc, (LARGURA//2 - desc.get_width()//2, 260))

        lbl_dif = fonte_bold.render("DENSIDADE DA REDE:", True, C_TEXT_WHITE)
        tela.blit(lbl_dif, (LARGURA//2 - lbl_dif.get_width()//2, 320))

        self.botoes_menu = []
        y_start = 360
        for i, nome in enumerate(DIFICULDADES.keys()):
            rect = pygame.Rect(LARGURA//2 - 120, y_start + (i * 60), 240, 45)
            self.botoes_menu.append((nome, rect))
            self.draw_button(tela, rect, nome, hover=rect.collidepoint(pos_mouse))

    def desenhar_hud(self, tela):
        panel = pygame.Surface((LARGURA, 80), pygame.SRCALPHA)
        panel.fill(C_UI_PANEL)
        pygame.draw.line(panel, C_NODE_BORDER, (0, 79), (LARGURA, 79), 1)
        tela.blit(panel, (0,0))

        lbl_modo = fonte_bold.render(f"MODO: {self.modo}", True, C_VISITADO)
        lbl_dif = fonte_ui.render(f"Nível: {self.dificuldade_atual}", True, C_TEXT_GREY)
        tela.blit(lbl_modo, (30, 15))
        tela.blit(lbl_dif, (30, 45))

        bar_w, bar_h = 300, 20
        bar_x, bar_y = LARGURA//2 - bar_w//2, 20
        pygame.draw.rect(tela, (20, 20, 20), (bar_x, bar_y, bar_w, bar_h), border_radius=10)
        pct = self.energia_atual / self.energia_max
        cor_vida = C_VISITADO if pct > 0.5 else (C_FILA if pct > 0.2 else C_ERROR)
        pygame.draw.rect(tela, cor_vida, (bar_x, bar_y, bar_w * pct, bar_h), border_radius=10)
        pygame.draw.rect(tela, C_TEXT_GREY, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=10)

        tempo_atual = (pygame.time.get_ticks() - self.start_ticks) / 1000
        lbl_time = fonte_bold.render(f"{tempo_atual:.1f}s", True, C_FILA)
        tela.blit(lbl_time, (LARGURA//2 - lbl_time.get_width()//2, 50))

        lbl_faltam = fonte_bold.render(f"RESTANTES: {len(self.gabarito)}", True, C_TEXT_WHITE)
        tela.blit(lbl_faltam, (LARGURA - 30 - lbl_faltam.get_width(), 30))

    def desenhar_input_nome(self, tela):
        overlay = pygame.Surface((LARGURA, ALTURA))
        overlay.set_alpha(240)
        overlay.fill((10, 12, 18))
        tela.blit(overlay, (0,0))
        
        t1 = fonte_titulo.render("NÍVEL CONCLUÍDO!", True, C_VISITADO)
        t_score = fonte_titulo.render(f"{self.pontuacao_final} Pts", True, C_FILA)
        t_tempo = fonte_ui.render(f"Tempo: {self.tempo_final:.2f}s | Vida: {int(self.energia_atual)}%", True, C_TEXT_GREY)
        t_inst = fonte_bold.render("Digite seu nome e pressione ENTER:", True, C_TEXT_WHITE)
        
        cx = LARGURA//2
        tela.blit(t1, (cx - t1.get_width()//2, 150))
        tela.blit(t_score, (cx - t_score.get_width()//2, 220))
        tela.blit(t_tempo, (cx - t_tempo.get_width()//2, 280))
        tela.blit(t_inst, (cx - t_inst.get_width()//2, 340))
        
        input_rect = pygame.Rect(cx - 150, 380, 300, 50)
        pygame.draw.rect(tela, C_BG_GRID, input_rect, border_radius=8)
        pygame.draw.rect(tela, C_VISITADO, input_rect, 2, border_radius=8)
        
        nome_s = fonte_bold.render(self.nome_jogador, True, C_TEXT_WHITE)
        tela.blit(nome_s, (input_rect.centerx - nome_s.get_width()//2, input_rect.centery - nome_s.get_height()//2))

    def desenhar_ranking(self, tela, pos_mouse):
        overlay = pygame.Surface((LARGURA, ALTURA))
        overlay.set_alpha(250)
        overlay.fill((10, 12, 18))
        tela.blit(overlay, (0,0))

        chave = f"{self.modo}_{self.dificuldade_atual}"
        top_scores = self.recordes.get(chave, [])

        t1 = fonte_titulo.render(f"RANKING: {self.modo} - {self.dificuldade_atual}", True, C_FILA)
        tela.blit(t1, (LARGURA//2 - t1.get_width()//2, 50))
        
        header = fonte_ui.render("RANK   JOGADOR           PONTOS       TEMPO", True, C_TEXT_GREY)
        tela.blit(header, (LARGURA//2 - 200, 140))

        start_y = 180
        for i, (nome, pontos, tempo) in enumerate(top_scores):
            cor = C_VISITADO if i == 0 else C_TEXT_WHITE
            str_rank = f"{i+1}."
            str_nome = f"{nome[:10]:<10}"
            str_pts  = f"{pontos:^10}"
            str_tmp  = f"{tempo:.1f}s"
            
            t_rank = fonte_bold.render(str_rank, True, cor)
            t_nome = fonte_bold.render(str_nome, True, cor)
            t_pts  = fonte_bold.render(str_pts, True, C_FILA)
            t_tmp  = fonte_bold.render(str_tmp, True, cor)
            
            y_pos = start_y + i*60
            tela.blit(t_rank, (LARGURA//2 - 200, y_pos))
            tela.blit(t_nome, (LARGURA//2 - 150, y_pos))
            tela.blit(t_pts,  (LARGURA//2 + 20, y_pos))
            tela.blit(t_tmp,  (LARGURA//2 + 180, y_pos))
            pygame.draw.line(tela, C_BG_GRID, (LARGURA//2 - 220, y_pos + 40), (LARGURA//2 + 250, y_pos + 40), 1)

        self.botao_voltar_menu = pygame.Rect(LARGURA//2 - 100, ALTURA - 80, 200, 40)
        self.draw_button(tela, self.botao_voltar_menu, "VOLTAR AO MENU", hover=self.botao_voltar_menu.collidepoint(pos_mouse))

    def desenhar_derrota(self, tela):
        overlay = pygame.Surface((LARGURA, ALTURA))
        overlay.set_alpha(200)
        overlay.fill((20, 10, 10))
        tela.blit(overlay, (0,0))
        t1 = fonte_titulo.render("FALHA CRÍTICA", True, C_ERROR)
        t2 = fonte_bold.render("Pressione [M] para o Menu", True, C_TEXT_WHITE)
        tela.blit(t1, (LARGURA//2 - t1.get_width()//2, ALTURA//2 - 50))
        tela.blit(t2, (LARGURA//2 - t2.get_width()//2, ALTURA//2 + 20))

    def draw(self, tela):
        self.desenhar_background(tela)
        pos_mouse = pygame.mouse.get_pos()

        if self.estado == ESTADO_MENU:
            self.desenhar_menu(tela, pos_mouse)
            return

        if self.estado in [ESTADO_JOGANDO, ESTADO_INPUT_NOME, ESTADO_DERROTA]:
            surface_glow = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            for u, v in self.edges:
                cor = C_VISITADO if (u.visitado and v.visitado) else C_EDGE
                largura = 2 if (u.visitado and v.visitado) else 1
                pygame.draw.line(tela, cor, (u.x, u.y), (v.x, v.y), largura)
            for node in self.nodes.values():
                node.desenhar(tela, surface_glow)
            tela.blit(surface_glow, (0,0))
            if self.no_atual:
                pygame.draw.circle(tela, C_ATUAL, (self.no_atual.x, self.no_atual.y), 6)
            
            if self.estado == ESTADO_JOGANDO:
                self.desenhar_hud(tela)

        if self.estado == ESTADO_INPUT_NOME:
            self.desenhar_input_nome(tela)
        elif self.estado == ESTADO_RANKING:
            self.desenhar_ranking(tela, pos_mouse)
        elif self.estado == ESTADO_DERROTA:
            self.desenhar_derrota(tela)

game = GraphGame()
clock = pygame.time.Clock()

rodando = True
while rodando:
    tela.fill(C_BG_DARK)
    game.update_hover(pygame.mouse.get_pos())
    
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        
        if evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1: 
                game.processar_clique(pygame.mouse.get_pos())
        
        if evento.type == pygame.KEYDOWN:
            if game.estado == ESTADO_INPUT_NOME:
                game.processar_input_nome(evento)
            elif evento.key == pygame.K_m:
                 if game.estado in [ESTADO_RANKING, ESTADO_DERROTA]:
                     game.estado = ESTADO_MENU

    game.draw(tela)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()