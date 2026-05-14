# Projeto de conversão RGB -> HSV

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
