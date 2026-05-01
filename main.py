import firebase_admin
from firebase_admin import  credentials, firestore
from appwrite.client import Client
from appwrite.services.storage import Storage
import numpy as np
import cv2
import os 
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import json
load_dotenv()


os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"]= "0"

from faceId import compare, compare2

# Configurando appwrite
appwriteClient = Client()
appwrite_end_point = os.environ['APPWRITE_END_POINT']
appwrite_project_id = os.environ.get('APPWRITE_PROJECT_ID')
appwrite_api_key = os.environ.get('APPWRITE_API_KEY')
appwriteClient.set_endpoint(appwrite_end_point)
appwriteClient.set_project(appwrite_project_id)
appwriteClient.set_key(appwrite_api_key)

storage = Storage(appwriteClient)


bucketId = os.environ.get('APPWRITE_BUCKET_ID')

print("✅ Conectado ao Appwrite.")


#Configuração inicial do Firebase.
firebase_credentials = os.environ.get('FIREBASE_CREDENTIALS')
cred_dict = json.loads(firebase_credentials)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()
print("✅ Conectado ao Firebase.")

# img1 = storage.get_file_download(bucketId, 'id_phenrique.limaaluno.uece.br')
# img2 = storage.get_file_download(bucketId, '69e8c56aed3105154b2b')

# img1 = np.frombuffer(img1, np.uint8)
# img1 = cv2.imdecode(img1, cv2.IMREAD_COLOR)

# img2 = np.frombuffer(img2, np.uint8)
# img2 = cv2.imdecode(img2, cv2.IMREAD_COLOR)

# print(compare(img1, img2))

def getImageFromAppWrite(bucketId, picId):
    img1 = storage.get_file_download(bucketId, picId)

    img1 = np.frombuffer(img1, np.uint8)
    img1 = cv2.imdecode(img1, cv2.IMREAD_COLOR)

    return img1

hoje = datetime.now(ZoneInfo("America/Fortaleza")).replace(hour=0, minute=0, second=0, microsecond=0)
inicio = hoje.astimezone(ZoneInfo("UTC"))
fim = inicio + timedelta(days=1)
ontem = inicio - timedelta(days=1)

print('\nPontos:')

def main(bucketId):
    records = db.collection_group('clockRecords').where("in", ">=", inicio).where("out", "<", fim).stream()


    for doc in records:
        ref = doc.reference
        userRef = ref.parent.parent
        result = 0
        try:
            record = doc.to_dict()
            if(not record.get('out') or not record.get('outPic')):
                ref.update({
                    "out":record['in'],
                    'verified': True,
                    'isValid': False,
                    'reason': 'Ponto incompleto'
                })
                userRef.update({
                    'atLab': False
                })
                print(userRef.id, 'Ponto incompleto')
                continue

            inPic = getImageFromAppWrite(bucketId, record['inPic'])
            outPic = getImageFromAppWrite(bucketId, record['outPic'])
    
            isSamePerson = compare(inPic, outPic)

            print('Comparando...')
            if(not isSamePerson and not compare2(inPic, outPic)):
                ref.update({
                    'verified': True,
                    'isValid': False,
                    'reason': 'Pontos divergentes'
                })
                print(userRef.id, 'Pontos divergentes')

                continue
            
            userId = userRef.id
            userId = 'id_' + userId.replace("@", "")
            userPic = getImageFromAppWrite(bucketId, userId)
            isSameUser = compare(inPic, userPic)

            if(not isSameUser and not compare2(inPic, userPic) and not compare2(outPic, userPic)):
                ref.update({
                    'verified': True,
                    'isValid': False,
                    'reason': 'Invalidado por faceID'
                })
                print(userRef.id, 'Invalidado por faceID')

                continue
            
            ref.update({
                    'verified': True,
                    'isValid': True
                })
            print(userId, 'Validado com sucesso')
        except Exception as e:
            print(f'Erro ao tentar varrer fotos de {userRef.id}: ${e}')
            print(userRef)
        finally:
            print(f'Fotos de {userRef.id} vasculhadas...')
            print('')


if __name__ == "__main__":
    main(bucketId)


# ontem = inicio - timedelta(days=1)
# print(inicio)
# print(ontem)

# records = db.collection_group('clockRecords').where("in", ">=", ontem).where("in", "<", inicio).stream()

# for doc in records:
#     ref = doc.reference
#     record = doc.to_dict()


#     userId = ref.parent.parent.id
#     print(record['in'])
#     print(userId)
    
#     print('\n============================================\n')
