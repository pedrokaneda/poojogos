import array
import math
import random
import sys

import pygame
import pygame.gfxdraw

# Inicialização do Pygame
pygame.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(16)

# Configurações da janela
LARGURA = 900
ALTURA = 600
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Batalha RPG")

# Cores
PRETO = (12, 14, 20)
PRETO_2 = (26, 30, 40)
AZUL = (60, 120, 220)
AZUL_CLARO = (110, 170, 255)
VERMELHO = (220, 60, 60)
VERMELHO_CLARO = (255, 110, 110)
VERDE = (50, 200, 90)
VERDE_CLARO = (120, 230, 145)
CINZA = (120, 128, 142)
CINZA_CLARO = (180, 185, 200)
AMARELO = (255, 220, 70)
BRANCO = (245, 247, 250)
DOURADO = (255, 200, 80)

# Fontes
FONTE = pygame.font.Font(None, 28)
FONTE_GRANDE = pygame.font.Font(None, 52)
FONTE_PEQUENA = pygame.font.Font(None, 24)
FONTE_BOTAO = pygame.font.Font(None, 30)

RELOGIO = pygame.time.Clock()


class SoundManager:
    def __init__(self):
        self.enabled = True

    def _gerar_tone(self, frequencias, duracao=0.12, volume=0.25):
        taxa = 22050
        total_amostras = int(taxa * duracao)
        buffer = array.array("h")

        for i in range(total_amostras):
            t = i / taxa
            envelope = min(1.0, t / 0.01) * max(0.0, 1.0 - (t / duracao))
            onda = 0.0
            for freq in frequencias:
                onda += math.sin(2 * math.pi * freq * t)
            valor = int(32767 * envelope * volume * (onda / len(frequencias)))
            buffer.append(max(-32768, min(32767, valor)))

        return pygame.mixer.Sound(buffer=buffer.tobytes())

    def play_ataque(self):
        if not self.enabled:
            return
        self._gerar_tone([180, 300], 0.10, 0.22).play()

    def play_hit(self):
        if not self.enabled:
            return
        self._gerar_tone([110, 170], 0.12, 0.30).play()

    def play_pocao(self):
        if not self.enabled:
            return
        self._gerar_tone([440, 660, 880], 0.17, 0.22).play()

    def play_defesa(self):
        if not self.enabled:
            return
        self._gerar_tone([90, 150], 0.08, 0.20).play()

    def play_vitoria(self):
        if not self.enabled:
            return
        self._gerar_tone([660, 880, 1100], 0.25, 0.18).play()

    def play_derrota(self):
        if not self.enabled:
            return
        self._gerar_tone([130, 90], 0.20, 0.20).play()


SOUND = SoundManager()


def clamp(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))


# ==========================================
# CLASSES DE PERSONAGENS
# ==========================================

class Personagem:
    def __init__(self, nome, vida, ataque, defesa):
        self.nome = nome
        self.vida_maxima = vida
        self.vida = vida
        self.ataque = ataque
        self.defesa = defesa

    def esta_vivo(self):
        return self.vida > 0

    def receber_dano(self, dano):
        dano_final = max(0, dano - self.defesa)
        self.vida = max(0, self.vida - dano_final)
        return dano_final

    def atacar(self, alvo):
        dano = random.randint(self.ataque - 5, self.ataque + 5)
        critico = random.random() < 0.2

        if critico:
            dano *= 2

        dano_causado = alvo.receber_dano(dano)
        return dano_causado, critico

    def curar(self, quantidade):
        vida_anterior = self.vida
        self.vida = min(self.vida_maxima, self.vida + quantidade)
        return self.vida - vida_anterior


class Jogador(Personagem):
    def __init__(self, nome):
        super().__init__(nome, 100, 20, 5)
        self.pocoes = 3
        self.nivel = 1
        self.xp = 0
        self.xp_para_proximo = 100

    def usar_pocao(self):
        if self.pocoes <= 0 or self.vida >= self.vida_maxima:
            return 0

        self.pocoes -= 1
        return self.curar(30)

    def ganhar_xp(self, quantidade):
        self.xp += quantidade
        while self.xp >= self.xp_para_proximo:
            self.xp -= self.xp_para_proximo
            self.nivel += 1
            self.xp_para_proximo = int(self.xp_para_proximo * 1.45)
            self.vida_maxima += 15
            self.ataque += 4
            self.defesa += 1
            self.vida = self.vida_maxima

    def status(self):
        return {
            "nivel": self.nivel,
            "xp": self.xp,
            "xp_total": self.xp_para_proximo,
        }


class Inimigo(Personagem):
    def __init__(self, nome, nivel=1):
        vida = 120 + (nivel - 1) * 20
        ataque = 15 + (nivel - 1) * 4
        defesa = 3 + (nivel - 1) * 2
        super().__init__(nome, vida, ataque, defesa)
        self.nivel = nivel
        self.xp_recompensa = 35 + nivel * 12


# ==========================================
# CLASSE BATALHA
# ==========================================

class Batalha:
    def __init__(self, jogador, nivel=1):
        self.jogador = jogador
        self.nivel = nivel
        self.inimigo = Inimigo(f"Goblin Nvl {nivel}", nivel)
        self.estado = "jogando"
        self.mensagem = "Escolha sua ação!"
        self.efeito_animacao = None
        self.tempo_animacao = 0
        self.efeitos = []

    def iniciar_efeito(self, tipo, lado):
        self.efeito_animacao = {"tipo": tipo, "lado": lado, "inicio": pygame.time.get_ticks()}

    def adicionar_explosao(self, x, y, cor=(255, 140, 80), duracao=18):
        self.efeitos.append({
            "x": x,
            "y": y,
            "cor": cor,
            "raio": 8,
            "velocidade": 4,
            "duracao": duracao,
            "vivo": True,
        })

    def atacar(self):
        if self.estado != "jogando":
            return

        self.iniciar_efeito("ataque", "jogador")
        SOUND.play_ataque()

        dano, critico = self.jogador.atacar(self.inimigo)

        if critico:
            self.mensagem = f"ATAQUE CRÍTICO! Você causou {dano} de dano!"
        else:
            self.mensagem = f"Você causou {dano} de dano!"

        self.verificar_vitoria()

        if self.estado == "jogando":
            self.turno_inimigo()

    def usar_item(self):
        if self.estado != "jogando":
            return

        cura = self.jogador.usar_pocao()

        if cura == 0:
            if self.jogador.pocoes == 0:
                self.mensagem = "Você não tem mais poções!"
            else:
                self.mensagem = "Sua vida já está cheia!"
            return

        SOUND.play_pocao()
        self.mensagem = f"Você recuperou {cura} de vida!"
        self.turno_inimigo()

    def defender(self):
        if self.estado != "jogando":
            return

        SOUND.play_defesa()
        dano = random.randint(self.inimigo.ataque - 5, self.inimigo.ataque + 5)
        dano = max(0, dano - self.jogador.defesa - 15)
        self.jogador.receber_dano(dano)

        self.mensagem = f"Você se defendeu! Recebeu {dano} de dano."
        self.verificar_vitoria()

        if self.estado == "jogando":
            self.turno_inimigo()

    def turno_inimigo(self):
        if not self.inimigo.esta_vivo() or self.estado != "jogando":
            return

        self.iniciar_efeito("ataque", "inimigo")
        SOUND.play_hit()

        dano, critico = self.inimigo.atacar(self.jogador)

        if critico:
            self.mensagem += f" O inimigo acertou um crítico de {dano}!"
        else:
            self.mensagem += f" O inimigo causou {dano} de dano!"

        self.verificar_vitoria()

    def verificar_vitoria(self):
        if not self.inimigo.esta_vivo():
            self.jogador.ganhar_xp(self.inimigo.xp_recompensa)
            self.estado = "vitoria"
            self.mensagem = f"Você venceu a batalha! +{self.inimigo.xp_recompensa} XP. Nível {self.jogador.nivel}!"
            self.adicionar_explosao(680, 350, (255, 120, 80))
            SOUND.play_vitoria()
        elif not self.jogador.esta_vivo():
            self.estado = "derrota"
            self.mensagem = "Você foi derrotado!"
            self.adicionar_explosao(220, 350, (255, 70, 70))
            SOUND.play_derrota()

    def reiniciar(self):
        self.jogador = Jogador("Herói")
        self.nivel = 1
        self.inimigo = Inimigo(f"Goblin Nvl {self.nivel}", self.nivel)
        self.estado = "jogando"
        self.mensagem = "Uma nova batalha começou!"
        self.efeito_animacao = None
        self.efeitos = []

    def proxima_fase(self):
        self.nivel += 1
        self.jogador.vida = self.jogador.vida_maxima
        self.jogador.pocoes = min(self.jogador.pocoes + 1, 5)
        self.inimigo = Inimigo(f"Goblin Nvl {self.nivel}", self.nivel)
        self.estado = "jogando"
        self.mensagem = f"Nova fase! O inimigo nível {self.nivel} apareceu! Você foi curado para continuar."
        self.efeito_animacao = None
        self.efeitos = []


# ==========================================
# FUNÇÕES GRÁFICAS
# ==========================================

def desenhar_texto(texto, fonte, cor, x, y, centro=False):
    superficie = fonte.render(texto, True, cor)
    if centro:
        x -= superficie.get_width() // 2
    TELA.blit(superficie, (x, y))


def desenhar_gradiente():
    for y in range(ALTURA):
        cor = (
            clamp(12 + y * 0.08, 0, 255),
            clamp(14 + y * 0.09, 0, 255),
            clamp(20 + y * 0.12, 0, 255),
        )
        pygame.draw.line(TELA, cor, (0, y), (LARGURA, y))


def desenhar_barra_vida(x, y, largura, altura, vida, vida_maxima):
    fundo = pygame.Rect(x, y, largura, altura)
    vida_rect = pygame.Rect(x, y, largura, altura)

    pygame.draw.rect(TELA, PRETO_2, fundo, border_radius=10)

    largura_atual = max(0, int((vida / vida_maxima) * largura)) if vida_maxima > 0 else 0
    vida_rect.width = largura_atual
    pygame.draw.rect(TELA, VERDE, vida_rect, border_radius=10)
    pygame.draw.rect(TELA, BRANCO, fundo, 2, border_radius=10)


def desenhar_botao(texto, x, y, largura, altura, cor, cor_texto=BRANCO):
    mouse = pygame.mouse.get_pos()
    retangulo = pygame.Rect(x, y, largura, altura)

    cor_atual = cor
    if retangulo.collidepoint(mouse):
        cor_atual = tuple(min(255, valor + 35) for valor in cor)

    pygame.draw.rect(TELA, cor_atual, retangulo, border_radius=14)
    pygame.draw.rect(TELA, BRANCO, retangulo, 2, border_radius=14)

    texto_surface = FONTE_BOTAO.render(texto, True, cor_texto)
    texto_x = x + (largura - texto_surface.get_width()) // 2
    texto_y = y + (altura - texto_surface.get_height()) // 2
    TELA.blit(texto_surface, (texto_x, texto_y))

    return retangulo


def desenhar_painel_personagem(x, y, largura, altura, nome, vida, vida_maxima, cor):
    painel = pygame.Rect(x, y, largura, altura)
    pygame.draw.rect(TELA, (22, 25, 35), painel, border_radius=18)
    pygame.draw.rect(TELA, cor, painel, 2, border_radius=18)

    desenhar_texto(nome, FONTE_GRANDE, BRANCO, x + 20, y + 15)
    desenhar_barra_vida(x + 20, y + 70, largura - 40, 18, vida, vida_maxima)
    desenhar_texto(f"Vida: {vida}/{vida_maxima}", FONTE, BRANCO, x + 20, y + 100)


def desenhar_bandeira(pos_x, pos_y, largura, altura, pais):
    bandeira = pygame.Rect(pos_x, pos_y, largura, altura)

    if pais == "israel":
        pygame.draw.rect(TELA, (255, 255, 255), bandeira)
        pygame.draw.rect(TELA, (0, 0, 0), (pos_x, pos_y + altura // 2 - 3, largura, 6))
        pygame.draw.rect(TELA, (0, 0, 0), (pos_x + largura // 2 - 3, pos_y, 6, altura))
        pygame.draw.rect(TELA, (0, 94, 184), (pos_x, pos_y + altura // 2 - 2, largura, 4))
        pygame.draw.rect(TELA, (0, 94, 184), (pos_x + largura // 2 - 2, pos_y, 4, altura))

    elif pais == "eua":
        pygame.draw.rect(TELA, (10, 49, 130), bandeira)
        for i in range(7):
            y = pos_y + i * (altura // 7)
            pygame.draw.rect(TELA, (255, 255, 255), (pos_x, y, largura, altura // 14))
        for i in range(7):
            x = pos_x + i * (largura // 7)
            pygame.draw.rect(TELA, (255, 255, 255), (x, pos_y, largura // 14, altura))
        pygame.draw.rect(TELA, (187, 19, 62), (pos_x, pos_y, largura // 2, altura // 2))

    elif pais == "russia":
        pygame.draw.rect(TELA, (255, 255, 255), bandeira)
        pygame.draw.rect(TELA, (0, 57, 166), (pos_x, pos_y, largura, altura // 3))
        pygame.draw.rect(TELA, (213, 43, 30), (pos_x, pos_y + 2 * altura // 3, largura, altura // 3))
        pygame.draw.rect(TELA, (255, 255, 255), (pos_x, pos_y + altura // 3, largura, altura // 3))


def desenhar_explosao(explosao):
    raio = explosao["raio"]
    cor = explosao["cor"]

    for i in range(5):
        d = int(raio + i * 8)
        pygame.draw.circle(TELA, cor, (explosao["x"], explosao["y"]), d, 3)

    pygame.draw.circle(TELA, (255, 255, 255), (explosao["x"], explosao["y"]), max(4, raio // 3), 2)


def atualizar_explosoes(batalha):
    novas = []
    for explosao in batalha.efeitos:
        explosao["raio"] += explosao["velocidade"]
        explosao["duracao"] -= 1
        if explosao["duracao"] > 0:
            novas.append(explosao)
    batalha.efeitos = novas


def desenhar_retrato(x, y, raio, cor, label, deslocamento=0, escala=1.0, tipo="mago", pais="israel"):
    pos_x = int(x + deslocamento)
    pos_y = int(y)
    raio_final = int(raio * escala)

    # brilho de fundo
    pygame.gfxdraw.filled_circle(TELA, pos_x, pos_y, int(raio_final + 18), (cor[0], cor[1], cor[2], 80))
    pygame.gfxdraw.aacircle(TELA, pos_x, pos_y, int(raio_final + 18), (cor[0], cor[1], cor[2], 120))

    # corpo base
    pygame.draw.circle(TELA, cor, (pos_x, pos_y), raio_final)
    pygame.draw.circle(TELA, BRANCO, (pos_x, pos_y), raio_final, 2)

    # Cabeça / rosto
    pygame.draw.circle(TELA, (240, 220, 190), (pos_x, pos_y - 10), max(10, raio_final // 3))

    # roupas / fantasia
    if tipo == "mago":
        pygame.draw.polygon(TELA, (120, 90, 220), [(pos_x - 24, pos_y + 20), (pos_x + 24, pos_y + 20), (pos_x + 14, pos_y + 58), (pos_x - 14, pos_y + 58)])
        pygame.draw.polygon(TELA, (180, 160, 255), [(pos_x - 15, pos_y - 38), (pos_x + 15, pos_y - 38), (pos_x, pos_y - 75)])
        pygame.draw.line(TELA, (255, 240, 120), (pos_x + 8, pos_y + 58), (pos_x + 28, pos_y + 92), 4)
        pygame.draw.line(TELA, (255, 240, 120), (pos_x - 8, pos_y + 58), (pos_x - 28, pos_y + 92), 4)
        pygame.draw.circle(TELA, (255, 220, 120), (pos_x, pos_y - 70), 8)

    elif tipo == "guerreiro":
        pygame.draw.rect(TELA, (70, 70, 80), (pos_x - 20, pos_y + 8, 40, 52), border_radius=8)
        pygame.draw.rect(TELA, (180, 180, 200), (pos_x - 28, pos_y + 20, 56, 18), border_radius=6)
        pygame.draw.line(TELA, (200, 200, 220), (pos_x - 8, pos_y + 62), (pos_x - 8, pos_y + 92), 5)
        pygame.draw.line(TELA, (200, 200, 220), (pos_x + 8, pos_y + 62), (pos_x + 8, pos_y + 92), 5)
        pygame.draw.polygon(TELA, (50, 120, 200), [(pos_x - 26, pos_y + 4), (pos_x + 26, pos_y + 4), (pos_x, pos_y - 26)])

    elif tipo == "assassino":
        pygame.draw.rect(TELA, (35, 35, 35), (pos_x - 18, pos_y + 10, 36, 52), border_radius=8)
        pygame.draw.polygon(TELA, (60, 60, 70), [(pos_x - 20, pos_y - 10), (pos_x + 20, pos_y - 10), (pos_x, pos_y - 45)])
        pygame.draw.line(TELA, (255, 90, 90), (pos_x + 18, pos_y + 18), (pos_x + 36, pos_y + 42), 4)
        pygame.draw.line(TELA, (255, 90, 90), (pos_x - 18, pos_y + 18), (pos_x - 36, pos_y + 42), 4)

    else:
        pygame.draw.rect(TELA, (90, 90, 90), (pos_x - 20, pos_y + 10, 40, 52), border_radius=8)
        pygame.draw.circle(TELA, (140, 80, 80), (pos_x, pos_y - 10), 12)

    # bandeira pequena na frente do personagem
    desenhar_bandeira(pos_x - 28, pos_y - 90, 26, 18, pais)
    desenhar_texto(label, FONTE, BRANCO, pos_x, pos_y + raio_final + 20, centro=True)


def desenhar_caixa_mensagem(mensagem):
    caixa = pygame.Rect(85, 445, 730, 58)
    pygame.draw.rect(TELA, (32, 36, 46), caixa, border_radius=14)
    pygame.draw.rect(TELA, DOURADO, caixa, 2, border_radius=14)

    texto = FONTE_PEQUENA.render(mensagem, True, BRANCO)
    TELA.blit(texto, (caixa.x + 18, caixa.y + 18))


def desenhar_status_jogador(jogador):
    texto = FONTE.render(f"Nível {jogador.nivel}   XP: {jogador.xp}/{jogador.xp_para_proximo}", True, AMARELO)
    TELA.blit(texto, (90, 260))


# ==========================================
# INTERFACE DO JOGO
# ==========================================

def desenhar_jogo(batalha):
    atualizar_explosoes(batalha)
    desenhar_gradiente()

    titulo = FONTE_GRANDE.render("BATALHA RPG", True, AMARELO)
    TELA.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 18))

    desenhar_painel_personagem(
        70, 90, 320, 150,
        batalha.jogador.nome,
        batalha.jogador.vida,
        batalha.jogador.vida_maxima,
        AZUL,
    )
    desenhar_painel_personagem(
        510, 90, 320, 150,
        batalha.inimigo.nome,
        batalha.inimigo.vida,
        batalha.inimigo.vida_maxima,
        VERMELHO,
    )

    desenhar_texto(f"Poções: {batalha.jogador.pocoes}", FONTE, AZUL_CLARO, 90, 255)
    desenhar_status_jogador(batalha.jogador)

    deslocamento_jogador = 0
    escala_jogador = 1.0
    deslocamento_inimigo = 0
    escala_inimigo = 1.0

    if batalha.efeito_animacao:
        tempo = pygame.time.get_ticks() - batalha.efeito_animacao["inicio"]
        progresso = min(1.0, tempo / 220)
        if batalha.efeito_animacao["lado"] == "jogador":
            deslocamento_jogador = math.sin(progresso * math.pi) * 28
            escala_jogador = 1.0 + 0.16 * math.sin(progresso * math.pi)
        else:
            deslocamento_inimigo = math.sin(progresso * math.pi) * 28
            escala_inimigo = 1.0 + 0.16 * math.sin(progresso * math.pi)

        if progresso >= 1.0:
            batalha.efeito_animacao = None

    desenhar_retrato(220, 350, 60, AZUL, "ISRAEL", deslocamento_jogador, escala_jogador, tipo="mago", pais="israel")
    desenhar_retrato(680, 350, 60, VERMELHO, "EUA", deslocamento_inimigo, escala_inimigo, tipo="assassino", pais="eua")

    for explosao in batalha.efeitos:
        desenhar_explosao(explosao)

    desenhar_bandeira(760, 90, 52, 30, "russia")

    desenhar_caixa_mensagem(batalha.mensagem)

    botoes = {}

    if batalha.estado == "jogando":
        botoes["atacar"] = desenhar_botao("ATACAR", 110, 520, 190, 48, VERMELHO)
        botoes["item"] = desenhar_botao("USAR POÇÃO", 355, 520, 190, 48, AZUL)
        botoes["defender"] = desenhar_botao("DEFENDER", 600, 520, 190, 48, CINZA)
    elif batalha.estado == "vitoria":
        botoes["reiniciar"] = desenhar_botao("PRÓXIMO NÍVEL", 325, 520, 250, 48, VERDE)
    else:
        botoes["reiniciar"] = desenhar_botao("REINICIAR", 325, 520, 250, 48, VERDE)

    pygame.display.flip()
    return botoes


# ==========================================
# LOOP PRINCIPAL
# ==========================================

def main():
    jogador = Jogador("Herói")
    batalha = Batalha(jogador, 1)
    executando = True

    while executando:
        botoes = desenhar_jogo(batalha)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                executando = False

            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                mouse = evento.pos

                if "atacar" in botoes and botoes["atacar"].collidepoint(mouse):
                    batalha.atacar()

                if "item" in botoes and botoes["item"].collidepoint(mouse):
                    batalha.usar_item()

                if "defender" in botoes and botoes["defender"].collidepoint(mouse):
                    batalha.defender()

                if "reiniciar" in botoes and botoes["reiniciar"].collidepoint(mouse):
                    if batalha.estado == "vitoria":
                        batalha.proxima_fase()
                    else:
                        batalha.reiniciar()

        RELOGIO.tick(60)

    pygame.quit()
    sys.exit()


def mainloop():
    main()


if __name__ == "__main__":
    mainloop()