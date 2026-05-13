import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, 
                             QHBoxLayout, QVBoxLayout, QFileDialog, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QOpenGLWidget
from OpenGL.GL import *

class OpenGLImageViewer(QOpenGLWidget):
    """
    o widget customizado (PyQt5) renderiza um array Numpy (imagem)
    usando texturas do OpenGL
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_data = None
        self.img_width = 0
        self.img_height = 0
        self.texture_id = None

    def atualiza(self, img_array):
        # recebe imagem, pega dimensões e atualiza widget
        self.img_height, self.img_width, _ = img_array.shape
        self.image_data = img_array
        self.update() 
        # dispara o evento que chama a função paintgl

    def initializeGL(self):
        # cor fundo padrão
        glClearColor(0.5, 0.5, 0.5, 1.0)
        glEnable(GL_TEXTURE_2D)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # projeção ortografica simles pra manter a proporção da imagem
        glOrtho(-1, 1, -1, 1, -1, 1)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        
        if self.image_data is None:
            return

        # na primeira vez, gera um ID de textura
        if self.texture_id is None:
            self.texture_id = glGenTextures(1)

        # associa a textura ao ID gerado e configura parâmetros de filtragem
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # os dados do array numpy sao transferidos para a memória de vídeo via opengl
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.img_width, self.img_height, 
                     0, GL_RGB, GL_UNSIGNED_BYTE, self.image_data)

        # desenha um quadrado e mapeia a textura em cima dele
        glBegin(GL_QUADS)
        # coordenadas gl invertidas em relação ao opencv 
        glTexCoord2f(0.0, 0.0); glVertex2f(-1.0, 1.0)   # Topo-Esquerda
        glTexCoord2f(1.0, 0.0); glVertex2f(1.0, 1.0)    # Topo-Direita
        glTexCoord2f(1.0, 1.0); glVertex2f(1.0, -1.0)   # Fundo-Direita
        glTexCoord2f(0.0, 1.0); glVertex2f(-1.0, -1.0)  # Fundo-Esquerda
        glEnd()


class ConvertApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("rgb2hsv")
        self.resize(900, 550)
        self.cv_img = None

        # widget e layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # botoes
        button_layout = QHBoxLayout()
        
        self.btn_carregar = QPushButton("carregar imagem")
        self.btn_carregar.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px; padding: 10px;")
        self.btn_carregar.clicked.connect(self.carrega)
        
        self.btn_converter = QPushButton("converter")
        self.btn_converter.setStyleSheet("background-color: #2196F3; color: white; font-size: 14px; padding: 10px;")
        self.btn_converter.setEnabled(False)
        self.btn_converter.clicked.connect(self.converte_hsv)

        button_layout.addWidget(self.btn_carregar)
        button_layout.addWidget(self.btn_converter)
        main_layout.addLayout(button_layout)

        # titulos
        title_layout = QHBoxLayout()
        lbl_orig = QLabel("original")
        lbl_orig.setAlignment(Qt.AlignCenter)
        lbl_orig.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        lbl_conv = QLabel("convertida (Manual)")
        lbl_conv.setAlignment(Qt.AlignCenter)
        lbl_conv.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        title_layout.addWidget(lbl_orig)
        title_layout.addWidget(lbl_conv)
        main_layout.addLayout(title_layout)

        # frame do opengl - imagens
        images_layout = QHBoxLayout()
        
        self.gl_img_original = OpenGLImageViewer()
        self.gl_img_hsv = OpenGLImageViewer()
        
        images_layout.addWidget(self.gl_img_original)
        images_layout.addWidget(self.gl_img_hsv)
        
        main_layout.addLayout(images_layout)
        main_layout.setStretch(2, 1)

    def carrega(self):
        options = QFileDialog.Options()
        caminho, _ = QFileDialog.getOpenFileName(
            "Imagens (*.jpg *.jpeg *.png *.bmp)", options=options
        )
        
        if not caminho:
            return
            
        self.cv_img = cv2.imread(caminho)
        
        img_rgb = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2RGB)
        self.gl_img_original.atualiza(img_rgb)
        
        self.btn_converter.setEnabled(True)
        self.gl_img_hsv.image_data = None
        self.gl_img_hsv.update()

    def converte_hsv(self):
        if self.cv_img is None:
            return

        # 1. converte a BGR nativa do opencv para rgb e normaliza para [0.0, 1.0]
        # [:, :, ::-1] inverte o último eixo de BGR para RGB de forma rápida
        img_rgb = self.cv_img[:, :, ::-1].astype(np.float32) / 255.0
        
        # separa canais
        R, G, B = img_rgb[:, :, 0], img_rgb[:, :, 1], img_rgb[:, :, 2]

        # encontra os valores Máximo (Value) e Mínimo entre R G e B pixel a pixel
        V = np.max(img_rgb, axis=2)
        Min = np.min(img_rgb, axis=2)
        
        # diferença entre o maior e menor - croma
        delta = V - Min 

        # 3. inicializa matrizes de H e S com zeros
        H = np.zeros_like(V)
        S = np.zeros_like(V)

        # 4. calc Saturação (S)
        # S = delta / V (mas se V for 0, matem S em 0)
        mask_v = V > 0
        S[mask_v] = delta[mask_v] / V[mask_v]

        # 5. calc Matiz (H) usando as equações e os fatores 0, 2, 4
        mask_delta = delta > 0

        # boolean masks que definem quem é o canal predominante do pixel
        idx_r = (V == R) & mask_delta
        idx_g = (V == G) & mask_delta
        idx_b = (V == B) & mask_delta

        # aplicando a lógica do Hue (com +0, +2, +4) e o multiplicador de 60
        # p/ vermelho - implicitamente +0
        H[idx_r] = (60.0 * ((G[idx_r] - B[idx_r]) / delta[idx_r]) + 360.0) % 360.0
        
        # p/ verde (+2 * 60 = 120)
        H[idx_g] = 60.0 * (((B[idx_g] - R[idx_g]) / delta[idx_g]) + 2.0)
        
        # p/ azul (+4 * 60 = 240)
        H[idx_b] = 60.0 * (((R[idx_b] - G[idx_b]) / delta[idx_b]) + 4.0)

        # 6. escala os resultados para o padrão do opecv uint8 de 8 bits
        # H entra no range [0, 179] (divide por 2), S e V entram no range [0, 255]
        H_cv = np.round(H / 2.0).astype(np.uint8)
        S_cv = np.round(S * 255.0).astype(np.uint8)
        V_cv = np.round(V * 255.0).astype(np.uint8)

        # 7. empilhar as 3 matrizes de volta para criar a imagem tridimensional
        img_hsv_manual = np.dstack((H_cv, S_cv, V_cv))

        # repassa os dados diretamente para o opengl
        self.gl_img_hsv.atualiza(img_hsv_manual)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConvertApp()
    window.show()
    sys.exit(app.exec_())