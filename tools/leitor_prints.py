import base64
import os
from pathlib import Path
from typing import Type
import pandas as pd
from crewai.tools import BaseTool
from openai import OpenAI
from pydantic import BaseModel, Field


class LeitorPrintsInput(BaseModel):
    pasta_prints: str = Field(..., description="Caminho da pasta contendo os prints e/ou planilhas Excel/CSV.")


class LeitorPrintsTool(BaseTool):
    name: str = "Leitor de Evidencias de Infraestrutura"
    description: str = (
        "Lê imagens (prints de Winbox, SADP, iVMS-4200, iDSecure, Digifort, AMT Remoto, Windows Server) "
        "e planilhas (.xlsx, .xls, .csv) dentro da pasta especificada e extrai todos os dados técnicos."
    )
    args_schema: Type[BaseModel] = LeitorPrintsInput

    def _run(self, pasta_prints: str) -> str:
        caminho = Path(pasta_prints)
        if not caminho.exists() or not caminho.is_dir():
            return f"Aviso: A pasta '{pasta_prints}' não existe."

        ext_img = {".png", ".jpg", ".jpeg", ".webp"}
        ext_tab = {".xlsx", ".xls", ".csv"}
        arquivos = sorted(caminho.iterdir())

        client = OpenAI(
            base_url=os.getenv("OPENAI_API_BASE", "http://127.0.0.1:31415/v1"),
            api_key=os.getenv("OPENAI_API_KEY", "sk-local"),
        )
        modelo = os.getenv("VISION_MODEL", "gemini-3-flash-preview")

        def sanitizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
            df_limpo = df.fillna("").copy()
            for col in df_limpo.columns:
                nome_col = str(col).strip().lower()
                if any(p in nome_col for p in ("senha", "password", "pass", "token", "chave", "secret")):
                    df_limpo[col] = "[OCULTO]"
                elif "anydesk" in nome_col:
                    df_limpo[col] = df_limpo[col].apply(
                        lambda x: f"***{str(x).strip().removesuffix('.0')[-3:]}"
                        if len(str(x).strip().removesuffix(".0")) >= 3
                        else "[OCULTO]"
                    )
            return df_limpo
        
        resultados = []
        for arq in arquivos:
            sufixo = arq.suffix.lower()

            if sufixo in ext_tab:
                if sufixo == ".csv":
                    df = sanitizar_dataframe(pd.read_csv(arq))
                    resultados.append(f"### Planilha: {arq.name}\n{df.to_markdown(index=False)}")
                else:
                    abas = pd.read_excel(arq, sheet_name=None)
                    for nome_aba, df in abas.items():
                        df = sanitizar_dataframe(df)
                        resultados.append(f"### Planilha: {arq.name} (Aba: {nome_aba})\n{df.to_markdown(index=False)}")

            elif sufixo in ext_img:
                mime = "image/png" if sufixo == ".png" else "image/jpeg"
                b64 = base64.b64encode(arq.read_bytes()).decode("utf-8")
                resp = client.chat.completions.create(
                    model=modelo,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        f"Analise este print técnico de infraestrutura (arquivo: {arq.name}). "
                                        f"Extraia TODOS os dados objetivos visíveis: IPs, máscaras, gateways, VLANs, "
                                        f"portas, regras NAT/firewall, modelos e status. Nunca invente dados."
                                    ),
                                },
                                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                            ],
                        }
                    ],
                )
                resultados.append(f"### Evidência do Print: {arq.name}\n{resp.choices[0].message.content}")

        if not resultados:
            return "Nenhum print ou planilha encontrado na pasta."

        return "\n\n---\n\n".join(resultados)