# Instale o pygame antes de executar este script:
# pip install pygame

import math
import random
import sys
import array
import pygame

# ============================================================
# INICIALIZAÇÃO
# ============================================================

pygame.init()

try:
    pygame.mixer.init()
    AUDIO_DISPONIVEL = True
except pygame.error:
    AUDIO_DISPONIVEL = False


LARGURA = 1100
ALTURA = 700

TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Batalha RPG")

RELOGIO = pygame.time.Clock()
FPS = 60


# ============================================================
# CORES
# ============================================================

PRETO = (8, 10, 16)
FUNDO = (13, 17, 27)
FUNDO_2 = (20, 25, 38)

BRANCO = (245, 247, 250)
CINZA = (130, 138, 155)
CINZA_ESCURO = (45, 51, 65)

AZUL = (55, 125, 235)
AZUL_CLARO = (100, 175, 255)

VERMELHO = (225, 65, 70)
VERMELHO_CLARO = (255, 110, 110)

VERDE = (55, 205, 105)
VERDE_CLARO = (115, 240, 155)

AMARELO = (255, 205, 70)
DOURADO = (255, 170, 55)

ROXO = (145, 90, 230)
ROXO_CLARO = (190, 140, 255)

LARANJA = (255, 125, 50)


# ============================================================
# FONTES
# ============================================================

FONTE_TITULO = pygame.font.Font(None, 68)
FONTE_GRANDE = pygame.font.Font(None, 48)
FONTE_MEDIA = pygame.font.Font(None, 34)
FONTE = pygame.font.Font(None, 27)
FONTE_PEQUENA = pygame.font.Font(None, 22)
FONTE_MINI = pygame.font.Font(None, 18)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def clamp(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))


def texto(superficie, mensagem, fonte, cor, x, y, centro=False):
    img = fonte.render(str(mensagem), True, cor)

    if centro:
        x -= img.get_width() // 2
        y -= img.get_height() // 2

    superficie.blit(img, (x, y))


def arredondar_retangulo(superficie, cor, rect, raio=12,
                         contorno=None, espessura=0):
    pygame.draw.rect(
        superficie,
        cor,
        rect,
        border_radius=raio
    )

    if contorno:
        pygame.draw.rect(
            superficie,
            contorno,
            rect,
            width=espessura if espessura > 0 else 1,
            border_radius=raio
        )


# ============================================================
# SISTEMA DE SOM
# ============================================================

class SoundManager:

    def __init__(self):
        self.enabled = AUDIO_DISPONIVEL
        self.sons = {}

    def _tone(self, frequencias, duracao=0.1, volume=0.2):

        if not self.enabled:
            return None

        taxa = 22050
        amostras = int(taxa * duracao)

        buffer = array.array("h")

        for i in range(amostras):

            t = i / taxa

            envelope = min(1, t / 0.015)

            envelope *= max(
                0,
                1 - t / duracao
            )

            onda = 0

            for freq in frequencias:
                onda += math.sin(
                    2 * math.pi * freq * t
                )

            onda /= len(frequencias)

            valor = int(
                32767 *
                onda *
                envelope *
                volume
            )

            buffer.append(
                max(-32768, min(32767, valor))
            )

        return pygame.mixer.Sound(
            buffer=buffer.tobytes()
        )

    def tocar(self, nome):

        if not self.enabled:
            return

        configuracoes = {

            "ataque": ([180, 280], 0.10, 0.22),

            "critico": ([300, 500, 700], 0.18, 0.25),

            "hit": ([100, 150], 0.12, 0.25),

            "cura": ([440, 660, 880], 0.22, 0.20),

            "defesa": ([80, 130], 0.10, 0.18),

            "vitoria": ([520, 660, 880, 1100], 0.40, 0.22),

            "derrota": ([180, 120, 80], 0.40, 0.20),

            "click": ([500], 0.05, 0.12),
        }

        if nome not in configuracoes:
            return

        frequencias, duracao, volume = configuracoes[nome]

        som = self._tone(
            frequencias,
            duracao,
            volume
        )

        if som:
            som.play()


SOM = SoundManager()


# ============================================================
# PARTÍCULAS
# ============================================================

class Particula:

    def __init__(self, x, y, cor, velocidade=None):

        self.x = x
        self.y = y

        self.cor = cor

        if velocidade is None:

            angulo = random.uniform(
                0,
                math.pi * 2
            )

            velocidade = random.uniform(
                2,
                6
            )

            self.vx = math.cos(angulo) * velocidade
            self.vy = math.sin(angulo) * velocidade

        else:
            self.vx, self.vy = velocidade

        self.vida = random.randint(
            25,
            55
        )

        self.vida_maxima = self.vida

        self.tamanho = random.randint(
            2,
            5
        )

    def atualizar(self):

        self.x += self.vx
        self.y += self.vy

        self.vx *= 0.97
        self.vy *= 0.97

        self.vy += 0.04

        self.vida -= 1

    def desenhar(self, tela):

        if self.vida <= 0:
            return

        alpha = self.vida / self.vida_maxima

        tamanho = max(
            1,
            int(self.tamanho * alpha)
        )

        pygame.draw.circle(
            tela,
            self.cor,
            (int(self.x), int(self.y)),
            tamanho
        )


class TextoFlutuante:

    def __init__(self, x, y, mensagem, cor):

        self.x = x
        self.y = y

        self.mensagem = mensagem
        self.cor = cor

        self.vida = 60

    def atualizar(self):

        self.y -= 0.7
        self.vida -= 1

    def desenhar(self, tela):

        if self.vida <= 0:
            return

        alpha = clamp(
            self.vida / 60,
            0,
            1
        )

        img = FONTE_MEDIA.render(
            self.mensagem,
            True,
            self.cor
        )

        # Pequena sombra
        sombra = FONTE_MEDIA.render(
            self.mensagem,
            True,
            PRETO
        )

        tela.blit(
            sombra,
            (
                int(self.x - img.get_width() / 2 + 2),
                int(self.y + 2)
            )
        )

        tela.blit(
            img,
            (
                int(self.x - img.get_width() / 2),
                int(self.y)
            )
        )


# ============================================================
# PERSONAGEM
# ============================================================

class Personagem:

    def __init__(
        self,
        nome,
        vida,
        ataque,
        defesa
    ):

        self.nome = nome

        self.vida_maxima = vida
        self.vida = vida

        self.ataque = ataque
        self.defesa = defesa

    def esta_vivo(self):

        return self.vida > 0

    def receber_dano(self, dano):

        dano_final = max(
            1,
            dano - self.defesa
        )

        self.vida = max(
            0,
            self.vida - dano_final
        )

        return dano_final

    def atacar(self, alvo):

        dano = random.randint(
            max(1, self.ataque - 5),
            self.ataque + 5
        )

        critico = random.random() < 0.18

        if critico:
            dano *= 2

        dano_causado = alvo.receber_dano(
            dano
        )

        return dano_causado, critico

    def curar(self, quantidade):

        vida_anterior = self.vida

        self.vida = min(
            self.vida_maxima,
            self.vida + quantidade
        )

        return self.vida - vida_anterior


# ============================================================
# JOGADOR
# ============================================================

class Jogador(Personagem):

    def __init__(self, nome):

        super().__init__(
            nome,
            120,
            24,
            7
        )

        self.nivel = 1

        self.xp = 0

        self.xp_para_proximo = 100

        self.pocoes = 3

        self.pocoes_maximas = 5

    def usar_pocao(self):

        if self.pocoes <= 0:
            return 0

        if self.vida >= self.vida_maxima:
            return 0

        self.pocoes -= 1

        return self.curar(35)

    def ganhar_xp(self, quantidade):

        niveis_ganhos = 0

        self.xp += quantidade

        while self.xp >= self.xp_para_proximo:

            self.xp -= self.xp_para_proximo

            self.nivel += 1

            niveis_ganhos += 1

            self.xp_para_proximo = int(
                self.xp_para_proximo * 1.35
            )

            self.vida_maxima += 18

            self.ataque += 4

            self.defesa += 1

            self.vida = self.vida_maxima

        return niveis_ganhos


# ============================================================
# INIMIGO
# ============================================================

class Inimigo(Personagem):

    TIPOS = [
        ("Goblin", VERDE),
        ("Orc", VERMELHO),
        ("Assassino", ROXO),
        ("Guardião", AZUL),
        ("Demônio", LARANJA)
    ]

    def __init__(self, nivel):

        nome_base, self.cor = self.TIPOS[
            min(
                nivel - 1,
                len(self.TIPOS) - 1
            )
        ]

        vida = 105 + (
            nivel - 1
        ) * 25

        ataque = 17 + (
            nivel - 1
        ) * 4

        defesa = 4 + (
            nivel - 1
        ) * 2

        super().__init__(
            f"{nome_base} Nível {nivel}",
            vida,
            ataque,
            defesa
        )

        self.nivel = nivel

        self.xp_recompensa = (
            45 + nivel * 15
        )


# ============================================================
# CLASSE BATALHA
# ============================================================

class Batalha:

    def __init__(self, jogador, inimigo):

        # Estrutura baseada no modelo do professor
        self.jogador = jogador
        self.inimigo = inimigo

        self.estado = "jogando"

        self.mensagem = (
            "Escolha uma ação para começar."
        )

        self.turno = 1

        self.particulas = []

        self.textos_dano = []

        self.animacao = None

        self.screen_shake = 0

        self.vitoria_processada = False

    # --------------------------------------------------------
    # EFEITOS
    # --------------------------------------------------------

    def criar_particulas(
        self,
        x,
        y,
        cor,
        quantidade=20
    ):

        for _ in range(quantidade):

            self.particulas.append(
                Particula(
                    x,
                    y,
                    cor
                )
            )

    def dano_visual(
        self,
        x,
        y,
        dano,
        critico=False
    ):

        cor = (
            AMARELO
            if critico
            else BRANCO
        )

        prefixo = (
            "CRÍTICO! "
            if critico
            else ""
        )

        self.textos_dano.append(
            TextoFlutuante(
                x,
                y,
                f"{prefixo}-{dano}",
                cor
            )
        )

    def iniciar_animacao(self, lado):

        self.animacao = {
            "lado": lado,
            "inicio": pygame.time.get_ticks()
        }

    # --------------------------------------------------------
    # ATAQUE
    # --------------------------------------------------------

    def atacar(self):

        if self.estado != "jogando":
            return

        self.iniciar_animacao(
            "jogador"
        )

        dano, critico = self.jogador.atacar(
            self.inimigo
        )

        SOM.tocar(
            "critico"
            if critico
            else "ataque"
        )

        self.criar_particulas(
            780,
            365,
            AMARELO
            if critico
            else LARANJA,
            28
        )

        self.dano_visual(
            780,
            315,
            dano,
            critico
        )

        if critico:

            self.mensagem = (
                f"ATAQUE CRÍTICO! "
                f"Você causou {dano} de dano!"
            )

        else:

            self.mensagem = (
                f"Você causou "
                f"{dano} de dano."
            )

        self.screen_shake = 8

        self.verificar_vitoria()

        if self.estado == "jogando":

            self.turno_inimigo()

    # --------------------------------------------------------
    # POÇÃO
    # --------------------------------------------------------

    def usar_item(self):

        if self.estado != "jogando":
            return

        cura = self.jogador.usar_pocao()

        if cura == 0:

            if self.jogador.pocoes <= 0:

                self.mensagem = (
                    "Você não possui mais poções."
                )

            else:

                self.mensagem = (
                    "Sua vida já está cheia."
                )

            return

        SOM.tocar("cura")

        self.criar_particulas(
            220,
            365,
            VERDE_CLARO,
            30
        )

        self.textos_dano.append(
            TextoFlutuante(
                220,
                315,
                f"+{cura} HP",
                VERDE_CLARO
            )
        )

        self.mensagem = (
            f"Você recuperou {cura} de vida."
        )

        self.turno_inimigo()

    # --------------------------------------------------------
    # DEFESA
    # --------------------------------------------------------

    def defender(self):

        if self.estado != "jogando":
            return

        SOM.tocar("defesa")

        dano_bruto = random.randint(
            max(
                1,
                self.inimigo.ataque - 5
            ),
            self.inimigo.ataque + 5
        )

        # Defesa reduz fortemente o dano
        dano = max(
            1,
            dano_bruto
            - self.jogador.defesa
            - 10
        )

        dano_real = self.jogador.receber_dano(
            dano
        )

        self.mensagem = (
            f"Você se defendeu! "
            f"Recebeu apenas {dano_real} de dano."
        )

        self.criar_particulas(
            220,
            365,
            AZUL_CLARO,
            20
        )

        self.screen_shake = 5

        self.verificar_vitoria()

        if self.estado == "jogando":

            self.turno += 1

            self.turno_inimigo()

    # --------------------------------------------------------
    # FUGA
    # --------------------------------------------------------

    def fugir(self):

        if self.estado != "jogando":
            return

        sucesso = random.random() < 0.65

        if sucesso:

            self.estado = "fuga"

            self.mensagem = (
                "Você conseguiu fugir da batalha!"
            )

        else:

            self.mensagem = (
                "Você tentou fugir, mas falhou!"
            )

            self.turno_inimigo()

    # --------------------------------------------------------
    # TURNO DO INIMIGO
    # --------------------------------------------------------

    def turno_inimigo(self):

        if (
            self.estado != "jogando"
            or not self.inimigo.esta_vivo()
        ):
            return

        self.turno += 1

        self.iniciar_animacao(
            "inimigo"
        )

        dano, critico = self.inimigo.atacar(
            self.jogador
        )

        SOM.tocar(
            "critico"
            if critico
            else "hit"
        )

        self.criar_particulas(
            220,
            365,
            VERMELHO_CLARO,
            20
        )

        self.dano_visual(
            220,
            315,
            dano,
            critico
        )

        if critico:

            self.mensagem = (
                f"O inimigo acertou um "
                f"CRÍTICO de {dano}!"
            )

        else:

            self.mensagem = (
                f"O inimigo causou "
                f"{dano} de dano."
            )

        self.screen_shake = 7

        self.verificar_vitoria()

    # --------------------------------------------------------
    # VITÓRIA / DERROTA
    # --------------------------------------------------------

    def verificar_vitoria(self):

        if not self.inimigo.esta_vivo():

            if not self.vitoria_processada:

                xp = self.inimigo.xp_recompensa

                niveis = self.jogador.ganhar_xp(
                    xp
                )

                self.mensagem = (
                    f"VITÓRIA! "
                    f"+{xp} XP"
                )

                if niveis > 0:

                    self.mensagem += (
                        f" | Você subiu "
                        f"para o nível "
                        f"{self.jogador.nivel}!"
                    )

                self.vitoria_processada = True

                self.estado = "vitoria"

                self.criar_particulas(
                    780,
                    365,
                    DOURADO,
                    70
                )

                SOM.tocar("vitoria")

        elif not self.jogador.esta_vivo():

            self.estado = "derrota"

            self.mensagem = (
                "DERROTA! "
                "Você foi derrotado."
            )

            self.criar_particulas(
                220,
                365,
                VERMELHO,
                50
            )

            SOM.tocar("derrota")

    # --------------------------------------------------------
    # PRÓXIMA FASE
    # --------------------------------------------------------

    def proxima_fase(self):

        novo_nivel = (
            self.inimigo.nivel + 1
        )

        self.jogador.vida = (
            self.jogador.vida_maxima
        )

        self.jogador.pocoes = min(
            self.jogador.pocoes + 1,
            self.jogador.pocoes_maximas
        )

        self.inimigo = Inimigo(
            novo_nivel
        )

        self.estado = "jogando"

        self.turno = 1

        self.mensagem = (
            f"Nova batalha! "
            f"{self.inimigo.nome} apareceu."
        )

        self.vitoria_processada = False

        self.particulas.clear()

        self.textos_dano.clear()

    # --------------------------------------------------------
    # ATUALIZAÇÃO
    # --------------------------------------------------------

    def atualizar(self):

        for particula in self.particulas[:]:

            particula.atualizar()

            if particula.vida <= 0:

                self.particulas.remove(
                    particula
                )

        for dano in self.textos_dano[:]:

            dano.atualizar()

            if dano.vida <= 0:

                self.textos_dano.remove(
                    dano
                )

        if self.screen_shake > 0:

            self.screen_shake *= 0.82

            if self.screen_shake < 0.5:

                self.screen_shake = 0


# ============================================================
# DESENHO DO FUNDO
# ============================================================

def desenhar_fundo(tela):

    for y in range(ALTURA):

        fator = y / ALTURA

        r = int(
            FUNDO[0] +
            (FUNDO_2[0] - FUNDO[0])
            * fator
        )

        g = int(
            FUNDO[1] +
            (FUNDO_2[1] - FUNDO[1])
            * fator
        )

        b = int(
            FUNDO[2] +
            (FUNDO_2[2] - FUNDO[2])
            * fator
        )

        pygame.draw.line(
            tela,
            (r, g, b),
            (0, y),
            (LARGURA, y)
        )

    # Grade discreta
    for x in range(0, LARGURA, 55):

        pygame.draw.line(
            tela,
            (25, 30, 43),
            (x, 0),
            (x, ALTURA)
        )

    for y in range(0, ALTURA, 55):

        pygame.draw.line(
            tela,
            (25, 30, 43),
            (0, y),
            (LARGURA, y)
        )


# ============================================================
# PERSONAGENS VISUAIS
# ============================================================

def desenhar_personagem(
    tela,
    x,
    y,
    cor,
    inimigo=False,
    escala=1
):

    x = int(x)
    y = int(y)

    r = int(62 * escala)

    # Aura
    for i in range(4):

        raio = r + 18 + i * 7

        cor_aura = tuple(
            max(
                0,
                min(
                    255,
                    int(cor[j] * 0.35)
                )
            )
            for j in range(3)
        )

        pygame.draw.circle(
            tela,
            cor_aura,
            (x, y),
            raio,
            2
        )

    # Sombra
    pygame.draw.ellipse(
        tela,
        (5, 7, 12),
        (
            x - 75,
            y + 75,
            150,
            30
        )
    )

    if inimigo:

        # Corpo
        pygame.draw.polygon(
            tela,
            cor,
            [
                (x - 45, y + 60),
                (x - 30, y - 10),
                (x, y - 45),
                (x + 30, y - 10),
                (x + 45, y + 60)
            ]
        )

        # Chifres
        pygame.draw.polygon(
            tela,
            (180, 180, 190),
            [
                (x - 35, y - 35),
                (x - 60, y - 75),
                (x - 25, y - 48)
            ]
        )

        pygame.draw.polygon(
            tela,
            (180, 180, 190),
            [
                (x + 35, y - 35),
                (x + 60, y - 75),
                (x + 25, y - 48)
            ]
        )

        # Olhos
        pygame.draw.circle(
            tela,
            AMARELO,
            (x - 20, y - 5),
            7
        )

        pygame.draw.circle(
            tela,
            AMARELO,
            (x + 20, y - 5),
            7
        )

        # Pupilas
        pygame.draw.circle(
            tela,
            PRETO,
            (x - 20, y - 5),
            3
        )

        pygame.draw.circle(
            tela,
            PRETO,
            (x + 20, y - 5),
            3
        )

    else:

        # Capa
        pygame.draw.polygon(
            tela,
            cor,
            [
                (x - 48, y + 60),
                (x - 35, y - 15),
                (x, y - 48),
                (x + 35, y - 15),
                (x + 48, y + 60)
            ]
        )

        # Cabeça
        pygame.draw.circle(
            tela,
            (224, 188, 155),
            (x, y - 25),
            28
        )

        # Capuz
        pygame.draw.polygon(
            tela,
            ROXO,
            [
                (x - 36, y - 35),
                (x, y - 75),
                (x + 36, y - 35),
                (x, y - 5)
            ]
        )

        # Olhos
        pygame.draw.circle(
            tela,
            BRANCO,
            (x - 10, y - 27),
            4
        )

        pygame.draw.circle(
            tela,
            BRANCO,
            (x + 10, y - 27),
            4
        )

        # Cajado
        pygame.draw.line(
            tela,
            (150, 105, 65),
            (x + 42, y + 60),
            (x + 65, y - 55),
            6
        )

        pygame.draw.circle(
            tela,
            AZUL_CLARO,
            (x + 65, y - 62),
            11
        )


# ============================================================
# BARRAS
# ============================================================

def desenhar_barra(
    tela,
    x,
    y,
    largura,
    altura,
    atual,
    maximo,
    cor
):

    fundo = pygame.Rect(
        x,
        y,
        largura,
        altura
    )

    pygame.draw.rect(
        tela,
        (30, 35, 48),
        fundo,
        border_radius=8
    )

    if maximo > 0:

        porcentagem = clamp(
            atual / maximo,
            0,
            1
        )

    else:

        porcentagem = 0

    preenchimento = pygame.Rect(
        x,
        y,
        int(largura * porcentagem),
        altura
    )

    pygame.draw.rect(
        tela,
        cor,
        preenchimento,
        border_radius=8
    )

    pygame.draw.rect(
        tela,
        (90, 98, 115),
        fundo,
        width=2,
        border_radius=8
    )


# ============================================================
# PAINEL
# ============================================================

def desenhar_painel_personagem(
    tela,
    personagem,
    x,
    y,
    largura,
    cor,
    jogador=False
):

    painel = pygame.Rect(
        x,
        y,
        largura,
        125
    )

    arredondar_retangulo(
        tela,
        (23, 28, 42),
        painel,
        18,
        cor,
        2
    )

    nome = personagem.nome

    texto(
        tela,
        nome,
        FONTE_MEDIA,
        BRANCO,
        x + 20,
        y + 15
    )

    texto(
        tela,
        f"HP {personagem.vida}/{personagem.vida_maxima}",
        FONTE_PEQUENA,
        CINZA,
        x + 20,
        y + 48
    )

    desenhar_barra(
        tela,
        x + 20,
        y + 72,
        largura - 40,
        20,
        personagem.vida,
        personagem.vida_maxima,
        cor
    )

    if jogador:

        texto(
            tela,
            f"ATK {personagem.ataque}   DEF {personagem.defesa}",
            FONTE_MINI,
            CINZA,
            x + 20,
            y + 100
        )

    else:

        texto(
            tela,
            f"ATK {personagem.ataque}   DEF {personagem.defesa}",
            FONTE_MINI,
            CINZA,
            x + 20,
            y + 100
        )


# ============================================================
# BOTÕES
# ============================================================

def botao(
    tela,
    rect,
    titulo,
    cor,
    mouse
):

    hover = rect.collidepoint(mouse)

    cor_atual = tuple(
        clamp(c + 25, 0, 255)
        for c in cor
    ) if hover else cor

    arredondar_retangulo(
        tela,
        cor_atual,
        rect,
        12,
        BRANCO,
        2
    )

    texto(
        tela,
        titulo,
        FONTE,
        BRANCO,
        rect.centerx,
        rect.centery,
        centro=True
    )

    return rect


# ============================================================
# MENU
# ============================================================

def desenhar_menu(tela, mouse):

    desenhar_fundo(tela)

    # brilho central
    pygame.draw.circle(
        tela,
        (25, 35, 65),
        (LARGURA // 2, 280),
        180
    )

    texto(
        tela,
        "BATALHA",
        FONTE_TITULO,
        BRANCO,
        LARGURA // 2,
        150,
        centro=True
    )

    texto(
        tela,
        "RPG",
        FONTE_TITULO,
        AMARELO,
        LARGURA // 2,
        215,
        centro=True
    )

    texto(
        tela,
        "Sistema de combate em Pygame",
        FONTE,
        CINZA,
        LARGURA // 2,
        275,
        centro=True
    )

    botao_iniciar = pygame.Rect(
        380,
        350,
        340,
        60
    )

    botao(
        tela,
        botao_iniciar,
        "INICIAR BATALHA",
        AZUL,
        mouse
    )

    botao_sair = pygame.Rect(
        380,
        430,
        340,
        60
    )

    botao(
        tela,
        botao_sair,
        "SAIR",
        VERMELHO,
        mouse
    )

    texto(
        tela,
        "ENTER  iniciar     ESC  sair",
        FONTE_PEQUENA,
        CINZA,
        LARGURA // 2,
        540,
        centro=True
    )

    return botao_iniciar, botao_sair


# ============================================================
# BATALHA - INTERFACE
# ============================================================

def desenhar_batalha(tela, batalha):

    desenhar_fundo(tela)

    # --------------------------------------------------------
    # SCREEN SHAKE
    # --------------------------------------------------------

    desloc_x = 0
    desloc_y = 0

    if batalha.screen_shake > 0:

        desloc_x = random.randint(
            -int(batalha.screen_shake),
            int(batalha.screen_shake)
        )

        desloc_y = random.randint(
            -int(batalha.screen_shake),
            int(batalha.screen_shake)
        )

    camada = pygame.Surface(
        (LARGURA, ALTURA),
        pygame.SRCALPHA
    )

    # --------------------------------------------------------
    # CABEÇALHO
    # --------------------------------------------------------

    texto(
        camada,
        "ARENA DE BATALHA",
        FONTE_GRANDE,
        BRANCO,
        LARGURA // 2,
        35,
        centro=True
    )

    texto(
        camada,
        f"FASE {batalha.inimigo.nivel}",
        FONTE_PEQUENA,
        AMARELO,
        LARGURA // 2,
        75,
        centro=True
    )

    # --------------------------------------------------------
    # PAINÉIS
    # --------------------------------------------------------

    desenhar_painel_personagem(
        camada,
        batalha.jogador,
        60,
        105,
        390,
        AZUL,
        True
    )

    desenhar_painel_personagem(
        camada,
        batalha.inimigo,
        650,
        105,
        390,
        VERMELHO,
        False
    )

    # --------------------------------------------------------
    # XP
    # --------------------------------------------------------

    texto(
        camada,
        f"NÍVEL {batalha.jogador.nivel}",
        FONTE_PEQUENA,
        AMARELO,
        60,
        245
    )

    desenhar_barra(
        camada,
        60,
        270,
        390,
        12,
        batalha.jogador.xp,
        batalha.jogador.xp_para_proximo,
        AMARELO
    )

    texto(
        camada,
        f"XP {batalha.jogador.xp}/"
        f"{batalha.jogador.xp_para_proximo}",
        FONTE_MINI,
        CINZA,
        455,
        267
    )

    # --------------------------------------------------------
    # ANIMAÇÃO
    # --------------------------------------------------------

    jogador_x = 250
    inimigo_x = 850

    jogador_escala = 1.0
    inimigo_escala = 1.0

    if batalha.animacao:

        tempo = (
            pygame.time.get_ticks()
            - batalha.animacao["inicio"]
        )

        progresso = min(
            1,
            tempo / 250
        )

        movimento = (
            math.sin(
                progresso * math.pi
            ) * 40
        )

        escala = (
            1 +
            0.12 *
            math.sin(
                progresso * math.pi
            )
        )

        if batalha.animacao["lado"] == "jogador":

            jogador_x += movimento

            jogador_escala = escala

        else:

            inimigo_x -= movimento

            inimigo_escala = escala

        if progresso >= 1:

            batalha.animacao = None

    desenhar_personagem(
        camada,
        jogador_x,
        410,
        AZUL,
        False,
        jogador_escala
    )

    desenhar_personagem(
        camada,
        inimigo_x,
        410,
        batalha.inimigo.cor,
        True,
        inimigo_escala
    )

    # VS
    texto(
        camada,
        "VS",
        FONTE_GRANDE,
        AMARELO,
        LARGURA // 2,
        410,
        centro=True
    )

    # --------------------------------------------------------
    # MENSAGEM
    # --------------------------------------------------------

    caixa_mensagem = pygame.Rect(
        210,
        495,
        680,
        55
    )

    arredondar_retangulo(
        camada,
        (25, 30, 43),
        caixa_mensagem,
        12,
        (80, 90, 110),
        2
    )

    texto(
        camada,
        batalha.mensagem,
        FONTE_PEQUENA,
        BRANCO,
        caixa_mensagem.centerx,
        caixa_mensagem.centery,
        centro=True
    )

    # --------------------------------------------------------
    # INFORMAÇÕES
    # --------------------------------------------------------

    texto(
        camada,
        f"Poções: {batalha.jogador.pocoes}",
        FONTE_PEQUENA,
        VERDE_CLARO,
        60,
        490
    )

    texto(
        camada,
        f"Turno: {batalha.turno}",
        FONTE_PEQUENA,
        CINZA,
        950,
        490
    )

    # --------------------------------------------------------
    # BOTÕES
    # --------------------------------------------------------

    botoes = {}

    mouse = pygame.mouse.get_pos()

    if batalha.estado == "jogando":

        botoes["atacar"] = botao(
            camada,
            pygame.Rect(
                115,
                585,
                200,
                60
            ),
            "ATACAR",
            VERMELHO,
            mouse
        )

        botoes["item"] = botao(
            camada,
            pygame.Rect(
                340,
                585,
                200,
                60
            ),
            "POÇÃO",
            VERDE,
            mouse
        )

        botoes["defender"] = botao(
            camada,
            pygame.Rect(
                565,
                585,
                200,
                60
            ),
            "DEFENDER",
            AZUL,
            mouse
        )

        botoes["fugir"] = botao(
            camada,
            pygame.Rect(
                790,
                585,
                200,
                60
            ),
            "FUGIR",
            CINZA_ESCURO,
            mouse
        )

    elif batalha.estado == "vitoria":

        botoes["proxima"] = botao(
            camada,
            pygame.Rect(
                350,
                585,
                400,
                60
            ),
            "PRÓXIMA FASE",
            DOURADO,
            mouse
        )

    elif batalha.estado == "derrota":

        botoes["reiniciar"] = botao(
            camada,
            pygame.Rect(
                350,
                585,
                400,
                60
            ),
            "TENTAR NOVAMENTE",
            VERMELHO,
            mouse
        )

    elif batalha.estado == "fuga":

        botoes["menu"] = botao(
            camada,
            pygame.Rect(
                350,
                585,
                400,
                60
            ),
            "VOLTAR AO MENU",
            AZUL,
            mouse
        )

    tela.blit(
        camada,
        (
            desloc_x,
            desloc_y
        )
    )

    # --------------------------------------------------------
    # PARTÍCULAS
    # --------------------------------------------------------

    for particula in batalha.particulas:

        particula.desenhar(tela)

    for dano in batalha.textos_dano:

        dano.desenhar(tela)

    return botoes


# ============================================================
# CRIAÇÃO DE BATALHA
# ============================================================

def nova_batalha():

    jogador = Jogador(
        "Herói"
    )

    inimigo = Inimigo(
        1
    )

    return Batalha(
        jogador,
        inimigo
    )


# ============================================================
# MAIN
# ============================================================

def main():

    estado_jogo = "menu"

    batalha = None

    executando = True

    while executando:

        mouse = pygame.mouse.get_pos()

        # ====================================================
        # EVENTOS
        # ====================================================

        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:

                executando = False

            # ------------------------------------------------
            # MENU
            # ------------------------------------------------

            if estado_jogo == "menu":

                if evento.type == pygame.KEYDOWN:

                    if evento.key == pygame.K_RETURN:

                        batalha = nova_batalha()

                        estado_jogo = "batalha"

                    elif evento.key == pygame.K_ESCAPE:

                        executando = False

                if evento.type == pygame.MOUSEBUTTONDOWN:

                    if evento.button == 1:

                        iniciar = pygame.Rect(
                            380,
                            350,
                            340,
                            60
                        )

                        sair = pygame.Rect(
                            380,
                            430,
                            340,
                            60
                        )

                        if iniciar.collidepoint(
                            evento.pos
                        ):

                            SOM.tocar("click")

                            batalha = nova_batalha()

                            estado_jogo = "batalha"

                        elif sair.collidepoint(
                            evento.pos
                        ):

                            executando = False

            # ------------------------------------------------
            # BATALHA
            # ------------------------------------------------

            elif estado_jogo == "batalha":

                if evento.type == pygame.KEYDOWN:

                    if evento.key == pygame.K_ESCAPE:

                        estado_jogo = "menu"

                    elif batalha.estado == "jogando":

                        if evento.key == pygame.K_1:
                            batalha.atacar()

                        elif evento.key == pygame.K_2:
                            batalha.usar_item()

                        elif evento.key == pygame.K_3:
                            batalha.defender()

                        elif evento.key == pygame.K_4:
                            batalha.fugir()

                if evento.type == pygame.MOUSEBUTTONDOWN:

                    if evento.button == 1:

                        # Os botões são recalculados
                        # durante o desenho.
                        botoes = desenhar_batalha(
                            TELA,
                            batalha
                        )

                        if (
                            "atacar" in botoes
                            and botoes["atacar"].collidepoint(
                                evento.pos
                            )
                        ):

                            SOM.tocar("click")
                            batalha.atacar()

                        elif (
                            "item" in botoes
                            and botoes["item"].collidepoint(
                                evento.pos
                            )
                        ):

                            SOM.tocar("click")
                            batalha.usar_item()

                        elif (
                            "defender" in botoes
                            and botoes["defender"].collidepoint(
                                evento.pos
                            )
                        ):

                            SOM.tocar("click")
                            batalha.defender()

                        elif (
                            "fugir" in botoes
                            and botoes["fugir"].collidepoint(
                                evento.pos
                            )
                        ):

                            SOM.tocar("click")
                            batalha.fugir()

                        elif (
                            "proxima" in botoes
                            and botoes["proxima"].collidepoint(
                                evento.pos
                            )
                        ):

                            batalha.proxima_fase()

                        elif (
                            "reiniciar" in botoes
                            and botoes["reiniciar"].collidepoint(
                                evento.pos
                            )
                        ):

                            batalha = nova_batalha()

                        elif (
                            "menu" in botoes
                            and botoes["menu"].collidepoint(
                                evento.pos
                            )
                        ):

                            estado_jogo = "menu"

        # ====================================================
        # ATUALIZAÇÃO
        # ====================================================

        if estado_jogo == "batalha" and batalha:

            batalha.atualizar()

        # ====================================================
        # DESENHO
        # ====================================================

        if estado_jogo == "menu":

            desenhar_menu(
                TELA,
                mouse
            )

        elif estado_jogo == "batalha":

            desenhar_batalha(
                TELA,
                batalha
            )

        pygame.display.flip()

        RELOGIO.tick(FPS)

    pygame.quit()
    sys.exit()


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()