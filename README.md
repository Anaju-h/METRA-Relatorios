# METRA — Sistema Inteligente de Pós-processamento de Relatórios

O **METRA** é um sistema desktop desenvolvido para auxiliar o pós-processamento de relatórios técnicos de metrologia, centralizando informações, automatizando etapas repetitivas e melhorando a organização, padronização e rastreabilidade dos processos.

O projeto foi desenvolvido com foco no fluxo de trabalho do **Centro de Excelência em Metrologia (CEM)**, permitindo consolidar documentos de medição, dados extraídos, características, imagens técnicas, marcações, informações de medição, controle técnico e emissão de relatórios finais.

## Objetivo

O objetivo do METRA é reduzir tarefas manuais envolvidas na preparação de relatórios de metrologia, permitindo que o usuário concentre seu trabalho na análise técnica e na validação das informações.

O sistema foi estruturado para automatizar o máximo possível sem eliminar a revisão humana, principalmente em dados extraídos automaticamente de relatórios de medição.

## Principais funcionalidades

* Criação e gerenciamento de processos de metrologia.
* Importação de um ou vários relatórios PDF.
* Identificação automática de processos de peça única ou lote.
* Extração de informações de relatórios de medição.
* Suporte inicial a relatórios CALYPSO e outras estruturas documentais.
* Identificação de peça, equipamento, operador e informações de medição.
* Extração e consolidação de características dimensionais.
* Análise de lotes e consolidação estatística.
* Gerenciamento de imagens técnicas.
* Editor de marcações em imagens.
* Vinculação de imagens e evidências ao processo.
* Registro das informações de medição.
* Controle técnico com elaboração, revisão e aprovação.
* Invalidação de aprovação após alterações relevantes no processo.
* Geração automática de relatórios técnicos em PDF.
* Templates específicos para diferentes tipos de inspeção.
* Anexação dos relatórios originais ao documento final.
* Versionamento de relatórios emitidos.
* Histórico e rastreabilidade das emissões.
* Conclusão e reabertura de processos.
* Central de processos com pesquisa e filtros.

## Tipos de relatório

Atualmente o sistema possui templates para:

* Inspeção dimensional de peça única.
* Inspeção dimensional em lote.
* Tomografia industrial.
* Relatório técnico personalizado.

Cada template utiliza uma estrutura específica de apresentação dos dados e pode incluir informações como resultados dimensionais, estatísticas, imagens, evidências, gráficos, observações e controle técnico.

## Fluxo principal

O fluxo de utilização do METRA segue, de forma geral, as seguintes etapas:

1. Criação de um novo processo.
2. Importação dos relatórios de origem.
3. Análise automática dos documentos.
4. Revisão das informações identificadas.
5. Criação do processo.
6. Consulta e revisão dos documentos.
7. Análise das características.
8. Preenchimento das informações de medição.
9. Inclusão de imagens e marcações.
10. Preenchimento e aprovação do controle técnico.
11. Preparação do relatório final.
12. Pré-visualização do documento.
13. Aprovação e exportação.
14. Registro da versão emitida.
15. Conclusão ou reabertura do processo.

## Arquitetura

O projeto foi organizado em camadas para separar responsabilidades e facilitar manutenção e evolução.

```text
METROREPORT/
│
├── assets/
│   ├── logos/
│   └── styles/
│
├── database/
│
├── models/
│
├── repositories/
│
├── services/
│   ├── document_analysis/
│   ├── report_engine/
│   └── report_templates/
│
├── ui/
│   ├── components/
│   ├── editor/
│   └── pages/
│
├── utils/
│
├── app.py
├── requirements.txt
└── README.md
```

### Models

Contêm as estruturas de dados utilizadas pelo sistema.

### Repositories

Responsáveis pelo acesso e persistência das informações no banco de dados.

### Services

Concentram as regras de negócio, análise documental, geração de relatórios, estatísticas, imagens, versionamento e demais operações da aplicação.

### UI

Contém as interfaces desenvolvidas em PySide6, incluindo páginas, componentes reutilizáveis e editor de imagens.

### Report Engine

Responsável pela montagem dos relatórios PDF técnicos utilizando layouts e renderizadores específicos para cada template.

## Tecnologias utilizadas

* Python
* PySide6
* SQLite
* PyMuPDF / Fitz
* Matplotlib
* Git
* GitHub

## Banco de dados

O sistema utiliza atualmente um banco de dados **SQLite local**.

Entre as informações persistidas estão:

* processos;
* documentos;
* extrações;
* características;
* informações de medição;
* imagens;
* marcações;
* controle técnico;
* versões de relatório.

Os dados locais utilizados durante execução e testes não são enviados ao repositório.

## Como executar

### 1. Clonar o repositório

```bash
git clone URL_DO_REPOSITORIO
```

### 2. Entrar na pasta do projeto

```bash
cd METRA-Relatorios
```

### 3. Criar um ambiente virtual

No Windows:

```bash
python -m venv .venv
```

### 4. Ativar o ambiente virtual

PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

### 5. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 6. Executar a aplicação

```bash
python app.py
```

## Status do projeto

**Em desenvolvimento — fase de refinamento e validação.**

A estrutura principal do sistema e o fluxo completo de geração de relatórios já estão implementados.

As próximas etapas estão concentradas em:

* correção de bugs de interface;
* testes integrados;
* revisão de consistência do fluxo;
* refinamento visual;
* melhoria da rastreabilidade;
* limpeza e refatoração do código;
* preparação da distribuição da aplicação;
* documentação final.

## Desenvolvimento

Projeto desenvolvido como solução para automação e melhoria do processo de preparação de relatórios técnicos de metrologia.

O desenvolvimento busca combinar automação, rastreabilidade, organização das informações e validação humana em um único fluxo de trabalho.

## Documentação

A documentação complementar do projeto está disponível em [`docs/`](docs/).

Ela inclui:

- checkpoints de desenvolvimento;
- arquitetura;
- banco de dados;
- fluxo do sistema;
- screenshots;
- materiais de apresentação.