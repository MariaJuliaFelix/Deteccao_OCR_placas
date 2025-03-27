import os  
import grpc  
from concurrent import futures  
import cv2  
import numpy as np  
import server_pb2  
import server_pb2_grpc  
import re  
from datetime import datetime  
import easyocr  
from ultralytics import YOLO  

plates_folder = 'plates'  
full_images_folder = 'full_images'   
os.makedirs(plates_folder, exist_ok=True)  
os.makedirs(full_images_folder, exist_ok=True)  

reader = easyocr.Reader(['pt'], gpu=True)  

def is_traditional_plate(text):  
    return bool(re.fullmatch(r'[A-Z]{3}[0-9]{4}', text))  

def is_mercosul_plate(text):  
    return bool(re.fullmatch(r'[A-Z]{3}[0-9]{1}[A-Z]{1}[0-9]{2}', text))  

similarNumbers = {  
    'B': '8', 'G': '6', 'I': '1', 'O': '0',   
    'S': '5', 'Z': '2', 'A': '4', 'D': '0'  
}  
similarLetters = {  
    '8': 'B', '6': 'G', '1': 'I', '0': 'O',   
    '5': 'S', '2': 'Z', '4': 'A'  
}  

def replace_similar_characters(text, confidence):  
    confidence_threshold = 0.8  
    if confidence < confidence_threshold:  
        return text  
    text = list(text)  
    for i, char in enumerate(text):  
        if char in similarNumbers:  
            text[i] = similarNumbers[char]  
            
    for i, char in enumerate(text):  
        if char in similarLetters:  
            text[i] = similarLetters[char]  

    return ''.join(text)  

def enhance_image(image):  
    return cv2.normalize(image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)  

def filter_plates(result):  
    for item in result:  
        text = ''.join(filter(str.isalnum, item[1])).upper()  
        confidence = item[2]  
        text = replace_similar_characters(text, confidence)  
        
        if is_traditional_plate(text):  
            return {"plate": text, "type": "Tradicional"}  
        elif is_mercosul_plate(text):  
            return {"plate": text, "type": "Mercosul"}  
    return None  

def np_image_to_bytes(image):  
    _, buffer = cv2.imencode('.jpg', image)  
    return buffer.tobytes()  

def save_plate_image(image, img_index, label, timestamp):  
    filename = f"{plates_folder}/{label}_{img_index}.jpg"  
    cv2.imwrite(filename, image)  
    return filename  

def save_full_image(image, img_index, label, timestamp):  
    filename = f"{full_images_folder}/full_image_{label}_{img_index}.jpg"  
    cv2.imwrite(filename, image)  
    return filename  

model_path = 'best.pt'   
model = YOLO(model_path)  

class PlateDatector(server_pb2_grpc.PlateDatectorServicer):  
    def StreamFrames(self, request_iterator, context):  
        for frame in request_iterator:  
            try:  
                image_data = np.frombuffer(frame.image, np.uint8)  
                image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)  
                print(f"Imagem carregada: {image.shape}") 

                roi_image = enhance_image(image)  

            
                cv2.imshow('link_da_camera', roi_image) 
                if cv2.waitKey(1) & 0xFF == ord('q'):    
                    print("Encerrando o vídeo...")  
                    cv2.destroyAllWindows()  
                    break  
                
                detections = model(roi_image)  
                print(f"Detecções encontradas: {len(detections[0].boxes)}") 
                plate_detected = False  
                plate_type = "Nenhuma"  
                plate_characters = ""  
                plate_folder = ""  
                full_image_folder = ""  
                
                for box in detections[0].boxes:  
                    x1, y1, x2, y2 = map(int, box.xyxy[0])  
                    roi = roi_image[y1:y2, x1:x2]  
                    cv2.rectangle(roi_image, (x1, y1), (x2, y2), (0, 255, 0), 2)  

                    result = reader.readtext(roi, detail=1)  
                    print(f"Resultado do OCR para ROI: {result}")   
                    plate_data = filter_plates(result)  

                    if plate_data:  
                        plate_detected = True  
                        plate_type = plate_data['type']  
                        plate_characters = plate_data['plate']  
                        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')  
                        img_index = len(os.listdir(plates_folder))  
                        
                        plate_folder = save_plate_image(roi, img_index, plate_data['plate'], timestamp)  
                        full_image_folder = save_full_image(roi_image, img_index, plate_data['plate'], timestamp)  

                        plate_image_bytes = np_image_to_bytes(roi)  
                        full_image_bytes = np_image_to_bytes(roi_image)  

                        print(f"Placa detectada: {plate_data['plate']} ({plate_data['type']}) salva em {plate_folder}")  
                        break  

                yield server_pb2.PlateResponse(  
                    characters=plate_characters,  
                    plate_type=plate_type,  
                    plate_folder=plate_folder,  
                    full_image_folder=full_image_folder,  
                    plate_image=plate_image_bytes if plate_detected else b'',  
                    full_image=full_image_bytes if plate_detected else b'',  
                    timestamp=datetime.now().strftime('%Y-%m-%d_%H-%M-%S')  
                )  

            except Exception as e:  
                print(f"Erro: {e}")  
                context.set_details(f"Erro: {str(e)}")  
                context.set_code(grpc.StatusCode.INTERNAL)  
                yield server_pb2.PlateResponse(characters="", plate_type="Erro", plate_folder="", full_image_folder="", plate_image=b"", full_image=b"", timestamp="")  

def serve():  
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))  
    server_pb2_grpc.add_PlateDatectorServicer_to_server(PlateDatector(), server)  
    server.add_insecure_port('[::]:50051')  
    print("Servidor gRPC rodando na porta 50051...")  
    server.start()  
    server.wait_for_termination()  

if __name__ == '__main__':  
    serve()
