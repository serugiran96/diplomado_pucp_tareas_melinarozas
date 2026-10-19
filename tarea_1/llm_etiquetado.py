"""Supervisión débil con un LLM local (Qwen2.5-0.5B-Instruct, sin API de pago).

Para cada titular, el LLM ve un prompt estructurado con las 4 categorías y se lee la probabilidad
del primer token de cada categoría en su respuesta; la confianza es el softmax sobre esas 4 opciones.
Uso (desde tarea_1/):  python llm_etiquetado.py
"""
import os
import time
from datetime import date

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODELO = "Qwen/Qwen2.5-0.5B-Instruct"
CATS = ["politica", "economia", "deportes", "ciencia_tecnologia"]
SISTEMA = ("Eres un editor de un diario peruano. Clasifica el titular en UNA categoría: "
           "politica (gobierno, Congreso, partidos, elecciones, justicia, corrupción), "
           "economia (mercados, empresas, empleo, precios, impuestos, AFP, comercio), "
           "deportes (fútbol y cualquier otra disciplina deportiva), "
           "ciencia_tecnologia (ciencia, salud científica, espacio, tecnología, internet, IA, videojuegos). "
           "Responde solo con el nombre exacto de la categoría.")

tok = AutoTokenizer.from_pretrained(MODELO)
tok.padding_side = "left"
llm = AutoModelForCausalLM.from_pretrained(MODELO, torch_dtype=torch.float32).eval()
primeros = [tok.encode(c, add_special_tokens=False)[0] for c in CATS]
assert len(set(primeros)) == 4, tok.convert_ids_to_tokens(primeros)

df = pd.read_csv("datos/noticias.csv")
prompts = [tok.apply_chat_template([{"role": "system", "content": SISTEMA},
                                    {"role": "user", "content": f"Titular: {t}\nCategoría:"}],
                                   tokenize=False, add_generation_prompt=True) for t in df.titular]
filas, t0 = [], time.time()
with torch.no_grad():
    for i in range(0, len(prompts), 32):
        enc = tok(prompts[i:i + 32], return_tensors="pt", padding=True)
        pos = (enc.attention_mask.cumsum(-1) - 1).clamp(min=0)
        logits = llm(**enc, position_ids=pos).logits[:, -1, :]
        probs = torch.softmax(logits[:, primeros], dim=-1)
        for titular, p in zip(df.titular[i:i + 32], probs):
            k = int(p.argmax())
            filas.append({"titular": titular, "etiqueta_llm": CATS[k], "confianza": round(float(p[k]), 4),
                          "modelo_llm": f"local:{MODELO}", "fecha": date.today().isoformat()})
out = pd.DataFrame(filas)
out.to_csv("datos/etiquetas_llm.csv", index=False)
print(f"{len(out)} etiquetas en {time.time() - t0:.0f} s ({(time.time() - t0) / len(out) * 1000:.0f} ms/titular)")
print(out.etiqueta_llm.value_counts().to_dict())

aud = (out.merge(df[["titular", "bajada", "url"]], on="titular", how="left")
       .sample(20, random_state=42)[["titular", "bajada", "url", "etiqueta_llm", "confianza"]])
aud["etiqueta_humana"] = ""
aud.to_csv("datos/auditoria_llm_20.csv", index=False)
print("auditoría: datos/auditoria_llm_20.csv")
