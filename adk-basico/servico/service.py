"""O serviço que o agente usa como ferramenta.

Este arquivo é o **outro lado** do agente. Ele carrega um modelo já treinado
(`modelo.joblib`, aqui nesta pasta) e o expõe num endpoint HTTP. O agente, em
`triagem/agent.py`, chama esse endpoint como se fosse uma função sua.

O modelo estima o risco de um pedido da Lei de Acesso à Informação virar
recurso. Ele vem pronto: treinar não é o assunto desta pasta.

Repare que o caminho do modelo é relativo a ESTE arquivo, e não ao diretório de
onde você rodou o comando. Sem isso, `bentoml serve` funciona quando você está
dentro de `servico/` e falha quando você está um nível acima — um erro que
custa dez minutos de aula.
"""

from pathlib import Path

import bentoml
import joblib
import pandas as pd

MODELO = Path(__file__).parent / "modelo.joblib"


@bentoml.service(resources={"cpu": "1"})
class Triagem:

    def __init__(self):
        self.modelo = joblib.load(MODELO)

    @bentoml.api
    def risco(
        self,
        Esfera: str = "Federal",
        UF: str = "(vazio)",
        OrgaoDestinatario: str = "Ministério da Saúde",
        AssuntoPedido: str = "Saúde",
        FormaResposta: str = "Pelo sistema (com avisos por email)",
        OrigemSolicitacao: str = "Internet",
        Decisao: str = "Acesso Negado",
        prazo_dias: int = 20,
        mes_registro: int = 6,
    ) -> dict:
        pedido = pd.DataFrame([{
            "Esfera": Esfera,
            "UF": UF,
            "OrgaoDestinatario": OrgaoDestinatario,
            "AssuntoPedido": AssuntoPedido,
            "FormaResposta": FormaResposta,
            "OrigemSolicitacao": OrigemSolicitacao,
            "Decisao": Decisao,
            "prazo_dias": prazo_dias,
            "mes_registro": mes_registro,
        }])
        risco = self.modelo.predict_proba(pedido)[0][1]
        return {"risco_de_recurso": round(float(risco), 4)}
