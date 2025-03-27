# Deteccao_OCR_placas
Projeto com servidor e cliente conectados por gRPC. O cliente envia frames de uma câmera para o servidor usando Protocol Buffers. O servidor detecta placas, salva imagens em pastas (full frame e ROI), realiza OCR com EasyOCR, valida o tipo de placa e serializa os dados para envio ao cliente.
