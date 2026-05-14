# Visão Geral do Programa: Conversor e Ajuste RGB para HSV

<!-- Este documento descreve a arquitetura e o funcionamento geral da aplicação, que consiste em uma interface gráfica para carregar imagens, converter o espaço de cor de RGB para HSV matematicamente e permitir ajustes finos interativos nos canais de cor utilizando aceleração de hardware para a renderização. -->


## Fórmulas de Referência (Exemplo para o Verde)
- **Fórmula original:** `Hue = 120 + (((B - R) / Δ) * 60)`
- **Fórmula simplificada:** `Hue = 60 * (2 + ((B - R) / Δ))`

---

## O Círculo Cromático (Hue)
O **Hue** (Matiz) representa um ângulo em um círculo que vai de **0° até 360°**. 
Nesse círculo, as três cores primárias são perfeitamente equidistantes, separadas por **120° cada**:
- **Vermelho:** 0° (fica no grau 0°/360°)
- **Verde:** 120°
- **Azul:** 240°

---

## Lógica do Código: Identificando a Cor Dominante
O código vai encontrar qual é a cor dominante de cada pixel (se é **R**, **G** ou **B**). A partir disso, o código vai tentar encontrar qual é a "fatia" de cor dominante em que aquele pixel se encontra (a cor predominante estamos chamando de **V**).

---

## O Papel dos Parâmetros 0, 2 e 4
A fórmula geral (do código) multiplica o resultado por **60**. É aí que agem o **0, 2 e 4**. Eles são **multiplicadores de base** para deslocar o ângulo para a fatia correta:

* **Quando V = R (Vermelho é o predominante):**
  A cor base deve começar no 0°.
  `0 * 60° = 0°` ➔ Vai para a fatia dos 0° (ou seja, R).

* **Quando V = G (Verde é o predominante):**
  A cor base deve saltar para a fatia dos 120°. O código utiliza o valor `+2`.
  `2 * 60° = 120°` ➔ Vai para a fatia dos 120°.
  *(É por isso que, antes de multiplicar por 60, a fórmula soma +2.0)*.

*(Seguindo a mesma lógica, quando o Azul for predominante, o multiplicador será 4, pois `4 * 60° = 240°`)*.

---

## A Equação e o Ajuste Fino
Analisando a equação principal:

> `60 * ( ((B - R) / Δ) + [0, 2 ou 4] )`

- A fração **`((B - R) / Δ)`** representa somente o **ajuste fino**.
- A operação **`60 * [0, 2 ou 4]`** é quem vai determinar **em qual fatia do círculo cromático a âncora está**, e por conseguinte, qual cor é.
---

## Bibliotecas Utilizadas e Suas Funções

```bash
pip install opencv-python numpy PyQt5 PyOpenGL
```

O programa faz uso de diversas bibliotecas para gerenciar interface, processamento matemático e renderização visual:

* **`sys`**: Utilizada para interagir com o sistema operacional, especificamente para iniciar e encerrar o loop de execução da interface gráfica (`app.exec_()`).
* **`cv2` (OpenCV)**: Usada estritamente para a leitura do arquivo de imagem do disco (`cv2.imread`) e para a conversão inicial de BGR (padrão de leitura do OpenCV) para RGB (`cv2.cvtColor`), permitindo que a imagem original seja exibida com as cores corretas.
* **`numpy`**: O "motor" matemático do código. Como as imagens são tratadas como matrizes de pixels, o NumPy permite realizar operações matemáticas em todos os pixels simultaneamente (vetorização). Ele é usado para calcular os canais H, S e V manualmente, aplicar máscaras booleanas e realizar ajustes de limite (como o `np.clip` e manipulação de arrays com `np.dstack`).
* **`PyQt5` (QtWidgets, QtCore)**: Fornece toda a base da Interface Gráfica do Usuário (GUI). É responsável por criar a janela principal, organizar os botões, rótulos (labels), menus de seleção de arquivos, caixas de diálogo (para os ajustes) e os controles deslizantes (sliders).
* **`OpenGL.GL` e `QOpenGLWidget`**: Utilizadas para a exibição das imagens. Em vez de usar os visualizadores de imagem padrão do PyQt, o código cria um contexto OpenGL para renderizar as imagens usando aceleração da placa de vídeo. As imagens (matrizes NumPy) são convertidas em texturas 2D e mapeadas sobre coordenadas geométricas na tela, garantindo alta performance na atualização visual.

---

## O Que o Código Está Fazendo (Fluxo de Funcionamento)

A aplicação segue um fluxo de trabalho dividido em quatro etapas principais:

### 1. Inicialização da Interface (GUI) e OpenGL
Ao executar o script, a classe `ConvertApp` monta uma janela dividida em duas áreas de exibição principais (visualizadores OpenGL customizados) e uma barra superior com três botões: **Carregar Imagem**, **Converter** e **Ajustar HSV**. 

### 2. Carregamento da Imagem (`carrega`)
Quando o usuário clica em "carregar imagem", o programa abre um explorador de arquivos padrão do sistema. Ao escolher uma imagem, ela é lida pelo OpenCV, convertida para o padrão de cor de exibição visual (RGB) e enviada para o visualizador OpenGL da esquerda (`gl_img_original`). Isso também desbloqueia o botão de conversão.

### 3. Conversão Matricial para HSV (`converte_hsv`)
Ao invés de usar uma função pronta de conversão, o código implementa a matemática do espaço de cor "na mão" para fins didáticos/algorítmicos.
* O programa separa a imagem em três matrizes independentes de cores: Red, Green e Blue (R, G, B).
* Calcula-se o **Valor (V)** pegando a cor mais forte de cada pixel e o **Delta** (a diferença entre a cor mais forte e a mais fraca).
* A **Saturação (S)** é calculada com base na razão entre o Delta e o Valor máximo.
* O **Matiz (H)** é calculado distribuindo os pixels nas fatias do círculo cromático dependendo de qual cor primária é predominante.
* Por fim, os valores são reescalonados para se adequarem aos limites de armazenamento padrão do OpenCV: `H` de 0 a 179, e `S` e `V` de 0 a 255. O resultado é juntado novamente e exibido no visualizador da direita. A imagem convertida original é salva na memória (`self.base_hsv`) para não perder os dados originais durante os ajustes.

### 4. Ajuste Interativo de HSV (`aplica_ajustes`)
O botão "ajustar hsv" abre uma pequena janela flutuante com três *sliders* que permitem somar ou subtrair valores aos canais da imagem. Toda vez que um slider é movido, o programa:
* Pega os valores originais da imagem HSV salva na memória.
* **Matiz (Hue):** Aplica a soma e utiliza a operação de módulo (`% 180`) para garantir que o valor seja circular. Se passar de 179, ele volta para o 0 (dando a volta no círculo cromático).
* **Saturação e Valor:** Adiciona as mudanças, mas utiliza a função `np.clip(..., 0, 255)`. Isso funciona como um teto e um chão de vidro: os valores não podem ser menores que 0 nem maiores que 255, evitando distorções catastróficas ou erros de *overflow* nos bits da imagem.
* A nova imagem modificada é empilhada, reconstruída e imediatamente enviada para o visualizador OpenGL atualizar a tela.
