# 🗓️ Grade de Horários — Coordenação de Horários dos Professores

## 📋 Descrição do Projeto

O **Sistema de Coordenação de Horários** automatiza a geração da grade acadêmica semanal da Faculdade Impacta. O coordenador carrega três arquivos CSV (professores, turmas e salas), o sistema valida os dados, aplica as regras de negócio e produz uma grade otimizada pronta para exportação.

O coração do sistema é um algoritmo **Greedy Expandido**: ele percorre todos os grupos de turmas, tenta alocar aulas compartilhadas quando possível, usa desempate por carga horária do professor e garante que nenhuma regra seja violada. Quando um grupo não cabe junto em uma sala, o sistema faz *fallback* individual e tenta alocar cada turma separadamente, maximizando o número de alocações.

A interface web (Streamlit) guia o coordenador em quatro passos: upload dos arquivos, prévia dos dados, geração da grade e visualização interativa com filtros por professor e por turma. O arquivo `grade_final.csv` é salvo automaticamente e também pode ser baixado diretamente pelo navegador.

---

## 👥 Integrantes

| Nome | RA |
|---|---|
| Beatriz Carvalho Santos | 2501088 |
| Larissa da Silva Maschio | 2502786 |
| Mariana Braga Sevarolli | 2503868 |

**Instituição:** Faculdade Impacta — Engenharia de Software — SI NOITE 2A

---

## ⚙️ Pré-requisitos

- Python **3.10 ou superior**
- pip (gerenciador de pacotes Python)

Instale as dependências do projeto:

```bash
pip install pandas streamlit pytest
```

---

## 🚀 Como Executar

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/projeto-grade-de-horarios.git
cd projeto-grade-de-horarios
```

### 2. Instale as dependências

```bash
pip install pandas streamlit pytest
```

### 3. Prepare os arquivos CSV

Coloque os três arquivos na pasta `csv/` (crie a pasta se não existir):

```
csv/
├── professores.csv
├── turmas.csv
└── salas.csv
```

Veja a seção **Formato dos CSVs** para o esquema correto de cada arquivo.

### 4. Inicie a interface web

```bash
streamlit run app.py
```

O navegador abrirá automaticamente em `http://localhost:8501`.

### 5. (Opcional) Execute sem interface

Para rodar via código Python diretamente:

```python
from projeto import carregar_dados, gerar_grade, exportar_grade

data  = carregar_dados()
grade = gerar_grade(data)
exportar_grade(grade)   # salva em csv/grade_final.csv
```

---

## 🗂️ Estrutura de Arquivos

```
projeto-grade-de-horarios/
│
├── projeto.py                  ← Toda a lógica de negócio (alocação, validações,
│                                 exportação, pré-validação, relatório de falhas)
│
├── app.py                      ← Interface Streamlit (upload, visualização,
│                                 download — sem regras de negócio)
│
├── csv/
│   ├── professores.csv         ← Entrada: disponibilidade dos professores
│   ├── turmas.csv              ← Entrada: turmas e disciplinas
│   ├── salas.csv               ← Entrada: salas e laboratórios
│   ├── grade_final.csv         ← Saída: grade gerada automaticamente
│   └── falhas_alocacao.csv     ← Saída: relatório de turmas não alocadas
│                                  (criado somente se houver falhas)
│
├── testes/
│   ├── teste_01.py             ← Alocação básica
│   ├── teste_02.py             ← RNV_01 + RNV_02
│   ├── teste_03.py             ← ALOC_01 — trava professor
│   ├── teste_04.py             ← ALOC_02 — trava sala + turma
│   ├── teste_05.py             ← ALOC_03 — turmas compartilhadas
│   ├── teste_interface.py      ← INT_01 (upload e validação)
│   ├── teste_visualizador.py   ← INT_02 (grade visual)
│   ├── teste_exportacao.py     ← RF_8 (exportação CSV)
│   ├── teste_pre_validacao.py  ← PRE_01 (validação cruzada de CSVs)
│   └── teste_relatorio_falhas.py ← REL_01 (relatório de falhas)
│
└── README.md
```

---

## 📊 Formato dos CSVs de Entrada

### `professores.csv`

Uma linha por **slot de disponibilidade**. Professor com dois horários disponíveis aparece em duas linhas.

| Coluna | Tipo | Exemplo | Descrição |
|---|---|---|---|
| `matricula` | texto | `2023001` | Matrícula do professor |
| `nome` | texto | `Ana Souza` | Nome completo |
| `disciplina` | texto | `Banco de Dados` | Disciplina que pode lecionar |
| `dia` | texto | `Segunda` | Dia da semana disponível |
| `horario` | texto | `08:00` | Horário disponível (HH:MM) |

```csv
matricula,nome,disciplina,dia,horario
2023001,Ana Souza,Banco de Dados,Segunda,08:00
2023001,Ana Souza,Banco de Dados,Quarta,10:00
2023002,Carlos Lima,Algoritmos,Terça,10:00
```

---

### `turmas.csv`

Uma linha por turma. Disciplinas com componente teórico **e** laboratorial aparecem em duas linhas separadas.

| Coluna | Tipo | Exemplo | Descrição |
|---|---|---|---|
| `turma` | texto | `SI1` | Identificador da turma |
| `alunos` | inteiro | `30` | Quantidade de alunos |
| `disciplina` | texto | `Banco de Dados` | Disciplina da turma |
| `tipo` | texto | `Teorica` ou `Laboratorio` | Tipo da aula |

```csv
turma,alunos,disciplina,tipo
SI1,30,Banco de Dados,Teorica
SI1,30,Banco de Dados,Laboratorio
CC1,25,Banco de Dados,Teorica
```

---

### `salas.csv`

| Coluna | Tipo | Exemplo | Descrição |
|---|---|---|---|
| `sala` | texto | `Sala101` | Identificador da sala |
| `capacidade` | inteiro | `40` | Capacidade máxima de alunos |
| `tipo` | texto | `Sala` ou `Laboratorio` | Tipo do ambiente |

```csv
sala,capacidade,tipo
Sala101,40,Sala
Sala102,35,Sala
Lab01,25,Laboratorio
Lab02,20,Laboratorio
```

---

### `grade_final.csv` (arquivo de saída)

| Coluna | Exemplo | Descrição |
|---|---|---|
| `turma` | `SI1;CC1` | Turma(s) alocadas (`;` separa turmas compartilhadas) |
| `disciplina` | `Banco de Dados` | Disciplina da aula |
| `professor` | `Ana Souza` | Professor alocado |
| `sala` | `Sala101` | Sala utilizada |
| `dia` | `Segunda` | Dia da semana |
| `horario` | `08:00` | Horário da aula |

---

## 📐 Regras de Negócio Implementadas

| Código | Descrição |
|---|---|
| **RN_1** | Professor só pode lecionar disciplinas para as quais está habilitado |
| **RN_2** | Professor só pode ser alocado em seus horários disponíveis |
| **RN_3** | Professor não pode estar em mais de uma aula no mesmo horário |
| **RN_4** | Turma não pode ter mais de uma aula no mesmo horário |
| **RN_5** | Sala não pode ser usada por mais de uma aula no mesmo horário |
| **RN_6** | A sala deve comportar a quantidade total de alunos da(s) turma(s) |
| **RN_7** | Disciplinas de laboratório devem ser alocadas em laboratórios |
| **RN_8** | O sistema tenta encaixar o maior número possível de turmas (melhor esforço) |
| **RN_9** | Uma mesma disciplina pode atender múltiplas turmas simultaneamente |
| **RN_10** | Quando turmas compartilham uma aula, a capacidade considera a soma de alunos |
| **RN_11** | A carga horária do professor é preenchida ao máximo dentro de sua disponibilidade |
| **RN_12** | Em empate, é priorizado o professor com menor quantidade de aulas atribuídas |
| **RN_13** | Componentes teórico e laboratorial de uma disciplina são alocações independentes |

---

## 🧠 Algoritmo de Alocação (Greedy Expandido)

O algoritmo funciona como um **organizador de agenda**: tenta encaixar o máximo de compromissos possíveis, respeitando todas as restrições, sem desfazer o que já foi marcado.

**Passo a passo:**

1. **Agrupamento:** Turmas com a mesma disciplina e mesmo tipo (teórica ou laboratório) são agrupadas. Turmas teóricas e de laboratório da mesma disciplina são grupos separados — RN_13.

2. **Tentativa compartilhada:** Para cada grupo, o sistema tenta alocar todas as turmas juntas na mesma aula (mesmo professor, sala e horário). Isso atende RN_9 e RN_10 (soma de alunos).

3. **Desempate:** Quando mais de um professor está disponível para o mesmo slot, é escolhido o com menor número de aulas já alocadas — RN_12.

4. **Fallback individual:** Se o grupo não couber junto (sala sem capacidade para a soma, ou conflito de horário), o sistema tenta alocar cada turma separadamente para maximizar alocações — RN_8.

5. **Travas de conflito:** Em cada tentativa, três travas são checadas simultaneamente: o professor não pode estar em dois lugares (RN_3), a turma não pode ter duas aulas no mesmo horário (RN_4), e a sala não pode ser ocupada duas vezes (RN_5).

6. **Relatório de falhas:** Turmas que não puderam ser alocadas em nenhum cenário são registradas em `falhas_alocacao.csv` com o motivo provável.

---

## 🖥️ Telas do Sistema

O sistema é dividido em **quatro passos** na interface:

**Passo 1 — Upload dos arquivos CSV**
Três áreas de upload lado a lado (professores, turmas, salas). O sistema valida o formato, as colunas obrigatórias e os tipos numéricos imediatamente após o upload, exibindo erros em vermelho ou confirmação em verde.

**Passo 2 — Prévia dos dados carregados**
Exibe os três DataFrames em abas para o coordenador conferir o conteúdo antes de processar.

**Passo 3 — Geração da grade**
Antes do botão "Gerar Grade", o sistema exibe avisos de consistência cruzada (ex.: turma de laboratório sem sala de laboratório cadastrada). O botão fica bloqueado até que os três arquivos válidos estejam carregados.

**Passo 4 — Visualizador dinâmico**
Três perspectivas em abas:
- **Grade Visual:** tabela horários × dias com cartões coloridos por professor.
- **Por Professor:** mesma grade filtrada para um professor selecionado.
- **Por Turma:** lista detalhada das aulas de uma turma específica.

Turmas não alocadas aparecem em cartões laranja com diagnóstico do motivo. Um botão de download entrega o `falhas_alocacao.csv` diretamente pelo navegador.

---

## 🧪 Como Rodar os Testes

Execute todos os testes de uma vez:

```bash
pytest testes/ -v
```

Ou por arquivo:

```bash
# Pré-validação cruzada dos CSVs (22 testes)
pytest testes/teste_pre_validacao.py -v

# Relatório de falhas (16 testes)
pytest testes/teste_relatorio_falhas.py -v

# Alocação básica
pytest testes/teste_01.py -v

# Travas de conflito
pytest testes/teste_03.py testes/teste_04.py -v

# Turmas compartilhadas e desempate
pytest testes/teste_05.py -v
```