from deepface import DeepFace
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def compare2(img1, img2):
    result = DeepFace.verify(
        img1_path=img1,
        img2_path=img2,
        model_name="ArcFace",          # ⭐ melhor precisão
        detector_backend="opencv",     # ⚡ rápido e suficiente
        distance_metric="cosine",
        enforce_detection=False,       # evita crash em lote
        align=True                     # melhora precisão
    )
    return result['verified']

def compare(img1, img2):
    emb1 = DeepFace.represent(
        img1,
        model_name='ArcFace',
        detector_backend='retinaface'
    )[0]['embedding']   
    emb2 = DeepFace.represent(
        img2,
        model_name='ArcFace',
        detector_backend='retinaface'
        )[0]['embedding']

    
    result = cosine_similarity(emb1, emb2) 
    return result > 0.6