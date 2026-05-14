import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, 
                             QHBoxLayout, QVBoxLayout, QFileDialog, QLabel,
                             QDialog, QSlider, QFormLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QOpenGLWidget
from OpenGL.GL import *

class OpenGLImageViewer(QOpenGLWidget):
    # o widget customizado (PyQt5) renderiza um array Numpy (imagem)
    # usando texturas do OpenGL
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

class ajusteHSV(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ajuste hsv")
        self.setFixedSize(300, 150)
        layout = QFormLayout(self)

        # sliders hsv
        self.slider_h = QSlider(Qt.Horizontal)
        self.slider_h.setRange(-179, 179) 
        
        self.slider_s = QSlider(Qt.Horizontal)
        self.slider_s.setRange(-255, 255) 
        
        self.slider_v = QSlider(Qt.Horizontal)
        self.slider_v.setRange(-255, 255) 

        layout.addRow("hue:", self.slider_h)
        layout.addRow("saturation:", self.slider_s)
        layout.addRow("value:", self.slider_v)

        # a cada mexida no slide chama func aplica_ajustes do pai ConvertApp
        self.slider_h.valueChanged.connect(self.parent().aplica_ajustes)
        self.slider_s.valueChanged.connect(self.parent().aplica_ajustes)
        self.slider_v.valueChanged.connect(self.parent().aplica_ajustes)


class ConvertApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("rgb2hsv")
        self.resize(900, 550)
        self.cv_img = None
        self.base_hsv = None
        #salva o hsv original como base dos ajustes

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

        self.btn_ajustar = QPushButton("ajustar hsv")
        self.btn_ajustar.setStyleSheet("background-color: #FF9800; color: white; font-size: 14px; padding: 10px;")
        self.btn_ajustar.setEnabled(False)
        self.btn_ajustar.clicked.connect(self.abre_ajustes)

        button_layout.addWidget(self.btn_carregar)
        button_layout.addWidget(self.btn_converter)
        button_layout.addWidget(self.btn_ajustar) # Inserindo no layout
        main_layout.addLayout(button_layout)

        # titulos
        title_layout = QHBoxLayout()
        lbl_orig = QLabel("original")
        lbl_orig.setAlignment(Qt.AlignCenter)
        lbl_orig.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        lbl_conv = QLabel("convertida")
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
            self, "selecione uma imagem", "", 
            "Imagens (*.jpg *.jpeg *.png *.bmp)", options=options
        )
        
        if not caminho:
            return
            
        self.cv_img = cv2.imread(caminho)
        
        img_rgb = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2RGB)
        self.gl_img_original.atualiza(img_rgb)
        
        self.btn_converter.setEnabled(True)
        self.btn_ajustar.setEnabled(False)
        self.gl_img_hsv.image_data = None
        self.gl_img_hsv.update()

    def converte_hsv(self):
        if self.cv_img is None:
            return

        img_rgb = self.cv_img[:, :, ::-1].astype(np.float32) / 255.0
        
        R, G, B = img_rgb[:, :, 0], img_rgb[:, :, 1], img_rgb[:, :, 2]
        V = np.max(img_rgb, axis=2)
        Min = np.min(img_rgb, axis=2)
        delta = V - Min 

        H = np.zeros_like(V)
        S = np.zeros_like(V)

        mask_v = V > 0
        S[mask_v] = delta[mask_v] / V[mask_v]

        mask_delta = delta > 0
        idx_r = (V == R) & mask_delta
        idx_g = (V == G) & mask_delta
        idx_b = (V == B) & mask_delta

        H[idx_r] = (60.0 * ((G[idx_r] - B[idx_r]) / delta[idx_r]) + 360.0) % 360.0
        H[idx_g] = 60.0 * (((B[idx_g] - R[idx_g]) / delta[idx_g]) + 2.0)
        H[idx_b] = 60.0 * (((R[idx_b] - G[idx_b]) / delta[idx_b]) + 4.0)

        H_cv = np.round(H / 2.0).astype(np.uint8)
        S_cv = np.round(S * 255.0).astype(np.uint8)
        V_cv = np.round(V * 255.0).astype(np.uint8)

        img_hsv_manual = np.dstack((H_cv, S_cv, V_cv))
        
        # salva o hsv original para usar como base dos ajustes
        self.base_hsv = img_hsv_manual.copy()
        self.btn_ajustar.setEnabled(True)

        self.gl_img_hsv.atualiza(img_hsv_manual)

    def abre_ajustes(self):
        self.janela_ajustes = ajusteHSV(self)
        self.janela_ajustes.show()

    def aplica_ajustes(self):
        if self.base_hsv is None:
            return
            
        # pega os valores dos silders 
        dh = self.janela_ajustes.slider_h.value()
        ds = self.janela_ajustes.slider_s.value()
        dv = self.janela_ajustes.slider_v.value()
        
        # aqui ele extrai os canais da hsv original  
        # conv int16 e evita problemas de overflow no cálculo + e -
        H = self.base_hsv[:, :, 0].astype(np.int16)
        S = self.base_hsv[:, :, 1].astype(np.int16)
        V = self.base_hsv[:, :, 2].astype(np.int16)
        
        # matiz h é circular no OpenCV de 0 até 179
        #  ai a gent usa módulo para dar a volta correta
        H_novo = (H + dh) % 180
        
        # ja S e V são limitados rigidamente entre 0 e 255 - clip
        S_novo = np.clip(S + ds, 0, 255)
        V_novo = np.clip(V + dv, 0, 255)
        
        # empilha dinovo as matrizes e converte de volta pra unit8
        img_modificada = np.dstack((H_novo, S_novo, V_novo)).astype(np.uint8)
        
        # atualiza opengl
        self.gl_img_hsv.atualiza(img_modificada)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConvertApp()
    window.show()
    sys.exit(app.exec_())