# Frases para colar

Cole **uma** por vez, no `adk run` ou na caixa da interface web. Nada aqui é
segredo: pode projetar esta página na tela.

---

## A. Ambíguas — e o que costuma acontecer de verdade

A frase tem dois sentidos possíveis, e cada agente tem que escolher um sem
saber o que os outros escolheram.

**Não conte com a divergência.** Testado com o Gemini: em "Vi o homem no
morro com o telescópio" os três leram o telescópio como instrumento de quem
vê, e nenhum considerou que o homem é que o carregava. Em "O professor disse
ao aluno que ele havia se enganado" os três entenderam que o errado foi o
aluno.

Isso não estraga a demonstração, muda o que ela mostra: três agentes que não
se falaram chegaram na MESMA leitura, porque compartilham o mesmo viés de
treino. Independência não é diversidade. É um resultado melhor do que o
esperado, e o relator o descreve certo — ele diz qual leitura todos adotaram
e qual ninguém considerou.

Se você quer divergência quase garantida, use o **grupo D**: o limite de 12
palavras força o agente `curta` a jogar fora algo que os outros dois
guardaram.

```
Vi o homem no morro com o telescópio.
```

```
O professor disse ao aluno que ele havia se enganado.
```

```
A comissão recomendou ao gestor que revisse a sua decisão.
```

```
Não é permitido consumir alimentos na sala de leitura aos domingos.
```

```
O relatório do auditor que estava incompleto foi devolvido.
```

```
Contratam-se profissionais para atendimento de clientes exigentes.
```

---

## B. Burocratês — a versão simples tem trabalho de verdade

```
Fica estabelecido que o interessado deverá proceder à juntada da documentação comprobatória no prazo improrrogável de 15 (quinze) dias, sob pena de arquivamento do feito.
```

```
Em atenção ao pleito formulado, informamos que a demanda encontra-se em fase de análise pela área técnica competente, não sendo possível, neste momento, precisar prazo para conclusão.
```

```
O indeferimento do pedido decorre da ausência de comprovação dos requisitos elencados no dispositivo legal supracitado.
```

```
Solicita-se a Vossa Senhoria a gentileza de providenciar o encaminhamento do referido expediente à unidade de destino.
```

---

## C. Jargão técnico — a versão simples tem que traduzir

```
O modelo apresentou overfitting no conjunto de treino, com AUC de 0,94 em treino e 0,61 em validação.
```

```
A latência do endpoint subiu para 800 ms no percentil 95 após o último deploy.
```

```
Recomenda-se a implementação de autenticação em dois fatores para mitigar o risco de comprometimento de credenciais.
```

```
O agente orquestra a chamada das ferramentas via function calling e persiste o resultado no estado da sessão.
```

---

## D. Compridas e redundantes — onde a divergência aparece

O limite de 12 palavras obriga o agente `curta` a descartar alguma coisa que
os outros dois mantiveram. A parte 3 do relatório ("alguém perdeu alguma
coisa?") existe para isso, e é aqui que ela tem o que dizer.

```
Gostaríamos de informar, desde já e com a devida antecedência, que a reunião anteriormente agendada para a próxima terça-feira foi, por motivos de força maior, transferida para a quinta-feira da mesma semana, no mesmo horário e no mesmo local de sempre.
```

```
É importante ressaltar que, conforme já mencionado anteriormente em oportunidades passadas, a participação de todos os membros da equipe é absolutamente fundamental e essencial para o pleno êxito da iniciativa.
```

```
Venho, por meio desta, respeitosamente, solicitar a gentileza de Vossa Senhoria no sentido de avaliar a possibilidade de concessão de prorrogação do prazo originalmente estipulado.
```

---

## E. Frases da própria turma

O melhor exercício é colar algo que apareceu na aula: uma linha do edital, um
trecho do e-mail que você recebeu hoje, uma frase do slide anterior. Se a
frase tiver nome de pessoa ou dado pessoal, troque por "Fulano" antes de
colar — o que você cola vai para a API do modelo.
