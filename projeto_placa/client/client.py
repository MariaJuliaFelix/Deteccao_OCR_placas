import grpc  
import cv2  
import client_pb2  
import client_pb2_grpc  
import json  
import os  
import numpy as np  

plates_folder = 'plates'  
full_images_folder = 'full_images'  
os.makedirs(plates_folder, exist_ok=True)  
os.makedirs(full_images_folder, exist_ok=True)  

def stream_frames(video_source, stub):  
    cap = cv2.VideoCapture(video_source)  
    try:  
        while cap.isOpened():  
            ret, frame = cap.read()  
            if not ret:  
                print("Erro ao capturar frame. Tentando novamente...")  
                continue   

            frame = cv2.resize(frame, (640, 480))    
            _, buffer = cv2.imencode('.jpg', frame)  
            frame_bytes = buffer.tobytes()  
            yield client_pb2.Frame(image=frame_bytes)  
    finally:  
        cap.release()  

def run_client(video_source):  
    with grpc.insecure_channel((f'localhost:50051')) as channel:  
        stub = client_pb2_grpc.PlateDatectorStub(channel)  
        responses = stub.StreamFrames(stream_frames(video_source, stub))  

        for response in responses:  
            data = {  
                "plate_characters": response.characters,  
                "plate_type": response.plate_type,  
                "timestamp": response.timestamp,  
                "plate_folder": response.plate_folder,  
                "full_image_folder": response.full_image_folder  
            }  
            if response.characters:  
                print(f"Resultado do OCR: {data['plate_characters']} ({data['plate_type']}) - Timestamp: {data['timestamp']} - Imagem cortada salva em: {data['plate_folder']} - Imagem completa salva em: {data['full_image_folder']}")  
                
                plate_image = np.frombuffer(response.plate_image, np.uint8)  
                plate_image = cv2.imdecode(plate_image, cv2.IMREAD_COLOR)  
                plate_image_filename = os.path.join(plates_folder, f"plate_{data['plate_characters']}.jpg")  
                cv2.imwrite(plate_image_filename, plate_image)  

                
                full_image = np.frombuffer(response.full_image, np.uint8)  
                full_image = cv2.imdecode(full_image, cv2.IMREAD_COLOR)  
                full_image_filename = os.path.join(full_images_folder, f"full_image_{data['plate_characters']}.jpg")  
                cv2.imwrite(full_image_filename, full_image)  
                
                with open('plates_data.json', 'a') as f:  
                    json.dump(data, f)  
                    f.write('\n')  

if __name__ == '__main__':  
    video_source = 'link_do_video'  
    run_client(video_source)
