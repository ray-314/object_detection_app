# ライブラリのインポート
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from googletrans import Translator
from PIL import Image
import json

# キーとエンドポイントの設定
with open('./key/secret.json') as f:
    secret = json.load(f)
KEY = secret['KEY']
ENDPOINT = secret['ENDPOINT']

# 認証とインスタンスの作成
computervision_client = ComputerVisionClient(ENDPOINT, CognitiveServicesCredentials(KEY))
tr = Translator(service_urls=['translate.googleapis.com'])

def get_tags(filepath, lang):
    """画像に含まれるコンテンツのタグ推定

    Args:
        filepath (str): 画像のファイルパス
        lang (str): 言語の選択

    Returns:
        list: 推定されたコンテンツタグ
    """
    # 言語の設定
    language = {
        '日本語': 'ja',
        '英語': 'en'
    }
    # 画像をバイナリデータで取得
    local_image = open(filepath, "rb")

    # コンテンツタグの推定
    tags_result = computervision_client.tag_image_in_stream(local_image, language=language[lang])
    local_image.close()
    tags = tags_result.tags
    tags_name = []
    for tag in tags:
        tags_name.append(tag.name)
        
    return tags_name


def detect_objects(filepath):
    """画像内のオブジェクトを検出する

    Args:
        filepath (str): 画像のファイルパス

    Returns:
        dict: 推定結果（json）
    """
    # 画像をバイナリデータで取得
    local_image = open(filepath, "rb")

    # オブジェクトの検出
    detect_objects_results = computervision_client.detect_objects_in_stream(local_image)
    objects = detect_objects_results.objects

    return objects

# ライブラリのインポート
import streamlit as st
from PIL import ImageDraw
from PIL import ImageFont

st.title('物体検出アプリ')

try:
    # 画像の選択
    st.markdown('### 画像の選択')
    uploaded_file = st.file_uploader('物体検出を試みたい画像を選択してください。', type=['jpg','png'])

    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        img_path = f'server_img/prepredict_img.jpg'
        img.save(img_path)

        # 言語の選択
        st.markdown('### 言語の選択')
        lang = st.selectbox(
            '物体検出の結果にはオブジェクト名が記載されています。その言語を選択してください。',
            ('日本語', '英語')
        )
        if lang=='日本語':
            font = ImageFont.truetype(font='./font/HanaMinA.ttf', size=50)
        else:
            font = ImageFont.truetype(font='./font/Helvetica 400.ttf', size=50)

        if st.button('開始'):
            comment = st.empty()
            comment.write('物体検出を開始します')
            objects = detect_objects(img_path)

            # 描画
            draw = ImageDraw.Draw(img)
            for object in objects:
                # 矩形の設定
                x = object.rectangle.x
                y = object.rectangle.y
                w = object.rectangle.w
                h = object.rectangle.h
                
                caption = object.object_property
                if lang=='日本語': caption = tr.translate(caption, dest="ja").text # 翻訳
                text_w, text_h = draw.textsize(caption, font=font)

                draw.rectangle([(x, y), (x+w, y+h)], fill=None, outline='green', width=5)
                draw.rectangle([(x, y), (x+text_w, y+text_h)], fill='green')
                draw.text((x, y), caption, fill='white', font=font)

            # 画像の表示
            st.image(img)

            # 画像のダウンロード
            img.save("server_img/predicted_img.png")
            with open("server_img/predicted_img.png", "rb") as file:
                btn = st.download_button(
                        label="ダウンロード",
                        data=file,
                        file_name="predict_img.png",
                        mime="image/png"
                    )

            # 認識されたコンテンツタグ
            st.markdown('### 認識されたコンテンツタグ')
            tags_name = get_tags(img_path, lang)
            tags_name = ', '.join(tags_name)
            st.markdown(f'> {tags_name}') 
            comment.write('完了しました')
except:
    st.error(
        "不具合が発生しています！リロードし直してみてください。"
    )