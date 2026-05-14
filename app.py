import streamlit as st
import anthropic
import base64
import json
import os
import re
from PIL import Image
import io

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

st.title("📦 Soma de Pré-Contagem")

fotos = st.file_uploader("Envie as fotos", type=["jpg","jpeg","png"], accept_multiple_files=True)

if fotos and st.button("🔍 Analisar e Somar"):
    todos_itens = []
    total_geral = 0

    for foto in fotos:
        # Comprime a imagem para menos de 5MB
        img = Image.open(foto)
        img = img.convert("RGB")
        buffer = io.BytesIO()
        quality = 85
        while True:
            buffer.seek(0)
            buffer.truncate()
            img.save(buffer, format="JPEG", quality=quality)
            if buffer.tell() < 4 * 1024 * 1024 or quality < 20:
                break
            quality -= 10

        img_b64 = base64.b64encode(buffer.getvalue()).decode()

        resposta = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
                    {"type": "text", "text": 'Analise o formulário. Retorne SOMENTE JSON: {"itens":[{"numero":1,"produto":"NOME","quantidade":30}],"total":96}'}
                ]
            }]
        )
        texto = resposta.content[0].text
        try:
            dados = json.loads(re.search(r'\{[\s\S]*\}', texto).group())
            todos_itens.extend(dados["itens"])
            total_geral += dados["total"]
            st.success(f"✅ {foto.name} — {dados['total']} unidades")
        except:
            st.error(f"❌ Erro em {foto.name}: {texto[:200]}")

    if todos_itens:
        st.subheader("📋 Itens encontrados")
        st.table(todos_itens)
        st.metric("TOTAL GERAL", total_geral)
