# 🚗 Detecção OCR de Placas

Este projeto implementa um sistema de **detecção e OCR** (Reconhecimento Óptico de Caracteres) de placas veiculares usando um **servidor** e **cliente** conectados via **gRPC**. O cliente envia frames capturados de uma câmera para o servidor, que processa as imagens, detecta as placas, realiza OCR para extrair os caracteres e valida o tipo de placa. O servidor então serializa os dados extraídos e os envia de volta ao cliente.

## Arquitetura

### Cliente

- **Função**: Envia frames capturados pela câmera para o servidor via **gRPC**.
- **Formato de Envio**: Cada frame é enviado como uma imagem compactada, utilizando **Protocol Buffers** (protobuf) para garantir a eficiência e compactação dos dados.

### Servidor

- **Recepção e Processamento**:
  - Recebe os frames do cliente e realiza a detecção de placas em cada imagem utilizando um modelo treinado.
  - Salva as imagens processadas em pastas específicas:
    - **full frame**: Imagem completa.
    - **ROI (Região de Interesse)**: Imagem destacando a placa.
  
- **OCR e Validação**:
  - Utiliza o **EasyOCR** para realizar a extração dos caracteres das placas detectadas.
  - Valida o tipo da placa (por exemplo, placas de veículos, comerciais, etc.).
  
- **Envio de Resultados**:
  - Serializa as informações extraídas (placa, tipo e dados) e envia de volta ao cliente.

## 📊 Dataset e Treinamento

O **dataset** utilizado foi criado por nós mesmos, visando melhorar a acurácia e robustez da detecção de placas. O processo de treinamento envolveu a coleta de imagens variadas de placas de veículos, considerando diferentes ângulos e condições de iluminação. Utilizamos técnicas de anotação para identificar as regiões das placas e os caracteres presentes em cada uma delas.

O **modelo treinado** foi otimizado para detectar placas com alta precisão e realizar o OCR de maneira eficiente.

## 🚀 Tecnologias Utilizadas

- **gRPC**: Comunicação cliente-servidor eficiente e de baixo custo.
- **Protocol Buffers**: Serialização de dados entre o cliente e o servidor.
- **EasyOCR**: Biblioteca para OCR, usada para extrair os caracteres das placas detectadas.
- **OpenCV**: Manipulação de imagens, incluindo captura de frames e detecção de placas.
