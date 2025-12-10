import pygame
import math
import random 
from collections import deque

# --- CONFIGURAÇÕES VISUAIS ---
LARGURA, ALTURA = 800, 600
COR_FUNDO = (30, 30, 30)
COR_NO = (200, 200, 200)
COR_ARESTA = (100, 100, 100)
COR_VISITADO = (50, 200, 50)     
COR_FILA = (200, 200, 50)        
COR_ATUAL = (200, 50, 50)        
COR_TEXTO = (255, 255, 255)
COR_BARRA_FUNDO = (50, 0, 0)
COR_BARRA_VIDA = (200, 0, 0)
COR_BOTAO = (70, 70, 100)
COR_BOTAO_ATIVO = (0, 150, 0) # Verde para o modo selecionado
COR_BOTAO_HOVER = (100, 100, 150)

# --- DIFICULDADES ---
DIFICULDADES = {
    "Noob":   {"camadas": 2, "ciclos": 0.0, "min_nos": 1, "max_nos": 2},
    "Fácil":  {"camadas": 3, "ciclos": 0.1, "min_nos": 2, "max_nos": 3},
    "Normal": {"camadas": 4, "ciclos": 0.3, "min_nos": 2, "max_nos": 4},
    "Pro":    {"camadas": 5, "ciclos": 0.5, "min_nos": 3, "max_nos": 5},
    "Professor": {"camadas": 10, "ciclos": 0.8, "min_nos": 8, "max_nos": 15}
}

# Estados do Jogo
ESTADO_MENU = 0
ESTADO_JOGANDO = 1
ESTADO_VITORIA = 2
ESTADO_DERROTA = 3

pygame.init()
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("AED Game: BFS & DFS")
fonte = pygame.font.SysFont('Arial', 20)
fonte_grande = pygame.font.SysFont('Arial', 40, bold=True)
fonte_pequena = pygame.font.SysFont('Arial', 16)

# --- CLASSE NODE ---
class Node:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.vizinhos = []
        self.visitado = False
        self.na_fila = False 

    def desenhar(self, tela):
        cor = COR_NO
        if self.visitado: cor = COR_VISITADO
        elif self.na_fila: cor = COR_FILA
        
        pygame.draw.circle(tela, cor, (self.x, self.y), 18)
        pygame.draw.circle(tela, (0,0,0), (self.x, self.y), 18, 2)
        
        texto = fonte.render(str(self.id), True, (0,0,0))
        tela.blit(texto, (self.x - 5, self.y - 10))

# --- CLASSE GRAPHGAME ---
class GraphGame:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.no_atual = None
        self.modo = "BFS" # Padrão inicial
        self.fila_esperada = deque() 
        self.gabarito = []
        
        self.estado = ESTADO_MENU
        self.energia_max = 100
        self.energia_atual = 100
        self.dificuldade_atual = "Normal"
        
        # Áreas clicáveis do menu
        self.botoes_menu_dificuldade = []
        self.botao_bfs = pygame.Rect(LARGURA//2 - 120, 100, 100, 40)
        self.botao_dfs = pygame.Rect(LARGURA//2 + 20, 100, 100, 40)

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

    def gerar_fase(self, config):
        self.nodes = {}
        self.edges = []
        self.gabarito = []
        self.energia_atual = self.energia_max
        
        num_camadas = config["camadas"]
        densidade_ciclos = config["ciclos"]
        min_nos = config["min_nos"]
        max_nos = config["max_nos"]

        margem_x = 50
        margem_y = 100
        altura_nivel = (ALTURA - margem_y - 50) // num_camadas

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
                jitter = random.randint(-20, 20) 
                x_pos = margem_x + (j * largura_setor) + (largura_setor // 2) + jitter
                y_pos = y_base + random.randint(-15, 15)
                
                novo_no = Node(id_counter, x_pos, y_pos)
                self.nodes[id_counter] = novo_no
                camada_atual.append(novo_no)
                id_counter += 1
                
                pai = random.choice(camada_anterior)
                self.add_edge(pai.id, novo_no.id)

            # Ciclos: Mais frequentes no BFS para mostrar rotas alternativas
            # Menos frequentes no DFS para evitar confusão extrema no início
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
                    
                    # No DFS iterativo, invertemos a ordem ao colocar na pilha
                    # para que ao fazer pop(), saia o menor ID primeiro
                    vizinhos_ordenados = sorted(atual.vizinhos, key=lambda n: n.id, reverse=True)
                    for vizinho in vizinhos_ordenados:
                        if vizinho.id not in visitados:
                            pilha.append(vizinho)
        
        print(f"Modo: {self.modo} | Gabarito: {self.gabarito}")

    def processar_clique(self, pos_mouse):
        if self.estado == ESTADO_MENU:
            # 1. Verifica clique nos botões de Modo (BFS/DFS)
            if self.botao_bfs.collidepoint(pos_mouse):
                self.modo = "BFS"
            elif self.botao_dfs.collidepoint(pos_mouse):
                self.modo = "DFS"
            
            # 2. Verifica clique nos botões de Dificuldade
            for nome, rect in self.botoes_menu_dificuldade:
                if rect.collidepoint(pos_mouse):
                    self.iniciar_nivel(nome)
            return

        if self.estado != ESTADO_JOGANDO:
            return

        for id, node in self.nodes.items():
            dist = math.hypot(pos_mouse[0] - node.x, pos_mouse[1] - node.y)
            if dist < 20: 
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
                self.estado = ESTADO_VITORIA
        else:
            self.energia_atual -= 15
            if self.energia_atual <= 0:
                self.energia_atual = 0
                self.estado = ESTADO_DERROTA

    def desenhar_menu(self, tela):
        # --- SEÇÃO 1: ESCOLHA O ALGORITMO ---
        titulo_algo = fonte.render("1. ESCOLHA O ALGORITMO:", True, COR_TEXTO)
        tela.blit(titulo_algo, (LARGURA//2 - titulo_algo.get_width()//2, 60))

        # Botão BFS
        cor_bfs = COR_BOTAO_ATIVO if self.modo == "BFS" else COR_BOTAO
        pygame.draw.rect(tela, cor_bfs, self.botao_bfs, border_radius=8)
        txt_bfs = fonte.render("BFS", True, COR_TEXTO)
        tela.blit(txt_bfs, (self.botao_bfs.centerx - txt_bfs.get_width()//2, self.botao_bfs.centery - txt_bfs.get_height()//2))
        
        # Botão DFS
        cor_dfs = COR_BOTAO_ATIVO if self.modo == "DFS" else COR_BOTAO
        pygame.draw.rect(tela, cor_dfs, self.botao_dfs, border_radius=8)
        txt_dfs = fonte.render("DFS", True, COR_TEXTO)
        tela.blit(txt_dfs, (self.botao_dfs.centerx - txt_dfs.get_width()//2, self.botao_dfs.centery - txt_dfs.get_height()//2))

        # Descrição do modo
        desc = "Regra: Visite todos os vizinhos (camada) antes de descer." if self.modo == "BFS" else "Regra: Vá o mais fundo possível antes de voltar."
        txt_desc = fonte_pequena.render(desc, True, (200, 200, 200))
        tela.blit(txt_desc, (LARGURA//2 - txt_desc.get_width()//2, 150))

        # --- SEÇÃO 2: ESCOLHA A DIFICULDADE ---
        titulo_dif = fonte.render("2. ESCOLHA A DIFICULDADE PARA INICIAR:", True, COR_TEXTO)
        tela.blit(titulo_dif, (LARGURA//2 - titulo_dif.get_width()//2, 200))
        
        self.botoes_menu_dificuldade = []
        y_start = 240
        for i, nome in enumerate(DIFICULDADES.keys()):
            rect = pygame.Rect(LARGURA//2 - 100, y_start + (i * 60), 200, 45)
            self.botoes_menu_dificuldade.append((nome, rect))
            
            mouse_pos = pygame.mouse.get_pos()
            cor = COR_BOTAO_HOVER if rect.collidepoint(mouse_pos) else COR_BOTAO
            
            pygame.draw.rect(tela, cor, rect, border_radius=10)
            pygame.draw.rect(tela, (255,255,255), rect, 2, border_radius=10)
            
            texto = fonte.render(nome, True, COR_TEXTO)
            tela.blit(texto, (rect.centerx - texto.get_width()//2, rect.centery - texto.get_height()//2))

    def desenhar_hud(self, tela):
        pygame.draw.rect(tela, COR_BARRA_FUNDO, (200, 10, 400, 30))
        largura_vida = 400 * (self.energia_atual / self.energia_max)
        pygame.draw.rect(tela, COR_BARRA_VIDA, (200, 10, largura_vida, 30))
        pygame.draw.rect(tela, (255,255,255), (200, 10, 400, 30), 2)
        
        texto = fonte.render(f"Energia: {int(self.energia_atual)}%", True, COR_TEXTO)
        tela.blit(texto, (350, 15))
        
        # Mostra qual algoritmo estamos jogando
        info = f"Modo: {self.modo} ({self.dificuldade_atual}) | Faltam: {len(self.gabarito)}"
        tela.blit(fonte.render(info, True, COR_TEXTO), (10, 50))

    def desenhar_fim(self, tela, texto_prin, cor_prin, texto_sec):
        overlay = pygame.Surface((LARGURA, ALTURA))
        overlay.set_alpha(220)
        overlay.fill((0, 0, 0))
        tela.blit(overlay, (0,0))
        
        t1 = fonte_grande.render(texto_prin, True, cor_prin)
        t2 = fonte.render(texto_sec, True, (255, 255, 255))
        t3 = fonte.render("Pressione 'M' para voltar ao Menu", True, (200, 200, 200))
        
        tela.blit(t1, (LARGURA//2 - t1.get_width()//2, ALTURA//2 - 50))
        tela.blit(t2, (LARGURA//2 - t2.get_width()//2, ALTURA//2 + 20))
        tela.blit(t3, (LARGURA//2 - t3.get_width()//2, ALTURA//2 + 60))

    def draw(self, tela):
        if self.estado == ESTADO_MENU:
            self.desenhar_menu(tela)
            return

        for u, v in self.edges:
            pygame.draw.line(tela, COR_ARESTA, (u.x, u.y), (v.x, v.y), 2)
        for node in self.nodes.values():
            node.desenhar(tela)
        
        self.desenhar_hud(tela)

        if self.estado == ESTADO_VITORIA:
            self.desenhar_fim(tela, "VITÓRIA!", (50, 255, 50), "Algoritmo executado com sucesso!")
        elif self.estado == ESTADO_DERROTA:
            self.desenhar_fim(tela, "GAME OVER", (255, 50, 50), "Você quebrou a lógica do algoritmo.")

# --- EXECUÇÃO ---
game = GraphGame()

rodando = True
while rodando:
    tela.fill(COR_FUNDO)
    
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        
        if evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1: 
                game.processar_clique(pygame.mouse.get_pos())
        
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_m and game.estado != ESTADO_JOGANDO:
                game.estado = ESTADO_MENU

    game.draw(tela)
    pygame.display.flip()

pygame.quit()