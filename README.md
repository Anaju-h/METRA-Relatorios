# METRA — Sistema Inteligente de Pós-processamento de Relatórios

O **METRA** é uma aplicação desktop desenvolvida para auxiliar o pós-processamento de relatórios técnicos de metrologia, centralizando informações, automatizando tarefas repetitivas e tornando o processo de elaboração de relatórios mais organizado, padronizado e rastreável.

O sistema foi desenvolvido considerando o fluxo de trabalho do **Centro de Excelência em Metrologia (CEM)** e permite reunir, em um único processo, documentos de medição, dados extraídos, características metrológicas, informações técnicas, imagens, marcações, controle técnico, versionamento e emissão do relatório final.

O METRA busca transformar os dados provenientes das inspeções em um relatório técnico consolidado, mantendo a **validação humana como parte fundamental do processo**.

---

## Objetivo

O objetivo do METRA é reduzir o trabalho manual envolvido na preparação e consolidação de relatórios de metrologia.

A aplicação foi projetada para automatizar as etapas em que a automação agrega eficiência, sem retirar do usuário a responsabilidade pela análise e validação das informações técnicas.

Entre os principais objetivos estão:

- centralizar as informações de cada processo;
- reduzir atividades repetitivas;
- apoiar a análise de relatórios de medição;
- padronizar a elaboração dos relatórios finais;
- organizar imagens e evidências técnicas;
- garantir revisão e aprovação antes da emissão;
- manter histórico e rastreabilidade;
- permitir diferentes tipos de relatório dentro do mesmo sistema.

---

## Principais funcionalidades

O METRA atualmente possui suporte para:

- criação e gerenciamento de processos de metrologia;
- identificação única dos processos;
- importação de um ou vários relatórios PDF;
- análise automática dos documentos importados;
- identificação de processos de peça única ou lote;
- suporte à interpretação de relatórios CALYPSO;
- extração de informações de peça e medição;
- extração e consolidação de características dimensionais;
- análise de resultados e tolerâncias;
- consolidação estatística para inspeções em lote;
- gerenciamento de imagens técnicas;
- definição de imagem principal do processo;
- classificação e inclusão de legendas nas imagens;
- editor de marcações e anotações;
- registro das informações de medição;
- controle técnico com elaboração, revisão e aprovação;
- invalidação da aprovação após alterações técnicas relevantes;
- seleção das seções que serão incluídas no relatório;
- geração automática de relatórios técnicos em PDF;
- pré-visualização do relatório antes da emissão oficial;
- templates específicos para diferentes tipos de inspeção;
- anexação dos documentos originais ao relatório consolidado;
- versionamento das emissões;
- histórico de versões;
- histórico de validação;
- inclusão opcional da rastreabilidade no PDF entregue;
- exportação do relatório final;
- conclusão e reabertura de processos;
- central de processos com pesquisa e filtros.

---

## Templates de relatório

O sistema possui atualmente quatro estruturas principais de relatório.

### Inspeção dimensional — peça única

Destinado à consolidação dos resultados dimensionais de uma única peça.

Pode apresentar identificação, informações da medição, características avaliadas, resultados, tolerâncias, gráficos, imagens, evidências e informações de aprovação.

### Inspeção dimensional — lote

Destinado à análise de várias unidades de uma mesma peça.

Além das informações individuais, permite consolidar os resultados do lote e apresentar indicadores e análises estatísticas.

### Tomografia industrial

Estrutura destinada a processos relacionados à inspeção por tomografia computadorizada, considerando informações e evidências específicas desse tipo de análise.

### Relatório técnico personalizado

Template flexível para situações que não dependem necessariamente de uma estrutura dimensional ou de dados estatísticos.

Permite organizar conteúdo técnico, descrições, observações, imagens, seções personalizadas e análise elaborada pelo usuário.

---

## Fluxo de utilização

O fluxo principal do METRA foi estruturado para acompanhar o processo desde a entrada dos documentos até a emissão do relatório.

```text
Novo processo
      ↓
Importação dos documentos
      ↓
Análise automática
      ↓
Revisão das informações identificadas
      ↓
Criação do processo
      ↓
Documentos e características
      ↓
Informações de medição
      ↓
Imagens e marcações
      ↓
Controle técnico
      ↓
Preparação do relatório
      ↓
Seleção das seções
      ↓
Pré-visualização
      ↓
Exportação oficial
      ↓
Registro da versão
      ↓
Conclusão do processo
```

Um processo concluído pode posteriormente ser **reaberto** quando houver necessidade de revisão ou de uma nova emissão.

---

## Geração do relatório final

A geração do relatório é realizada por um motor próprio de renderização, responsável por transformar as informações armazenadas no processo em um documento PDF consolidado.

Antes da emissão, o usuário pode selecionar quais conteúdos disponíveis devem fazer parte do relatório.

Entre eles podem estar:

- resumo e identificação;
- documentos e unidades;
- informações da medição;
- resultados metrológicos;
- imagens técnicas;
- observações;
- elaboração e aprovação;
- histórico de versões;
- histórico de validação.

As opções de **Histórico de versões** e **Histórico de validação** são opcionais e permanecem desmarcadas por padrão, permitindo manter informações internas de rastreabilidade fora do documento destinado ao cliente quando necessário.

A emissão oficial depende da aprovação do **Controle Técnico**.

---

## Rastreabilidade e versionamento

O METRA mantém mecanismos de rastreabilidade durante o ciclo de vida do processo.

Cada emissão oficial gera um registro de versão associado ao relatório.

Quando informações técnicas relevantes são modificadas após uma aprovação, o sistema pode invalidar a aprovação anterior, exigindo uma nova validação antes da próxima emissão.

O sistema mantém separadamente:

- versão atual do processo;
- versões oficialmente emitidas;
- data e hora das emissões;
- histórico de validação;
- situação do Controle Técnico.

Essas informações permanecem disponíveis internamente e podem, quando necessário, ser incluídas no relatório final.

---

## Controle Técnico

O Controle Técnico representa a etapa formal de validação do relatório.

O sistema permite registrar informações relacionadas à:

- elaboração;
- revisão;
- aprovação;
- responsáveis;
- datas;
- observações de controle.

A emissão oficial do relatório somente é liberada quando as condições necessárias de aprovação são atendidas.

No documento final, o Controle Técnico e as responsabilidades são posicionados no encerramento do relatório.

---

## Arquitetura

O projeto utiliza uma arquitetura em camadas para separar interface, regras de negócio, persistência e geração de documentos.

```text
METRA-Relatorios/
│
├── assets/
│   ├── logos/
│   └── styles/
│
├── database/
│
├── docs/
│
├── models/
│
├── repositories/
│
├── services/
│   ├── document_analysis/
│   ├── report_engine/
│   └── ...
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

Representam as principais entidades e estruturas de dados utilizadas pela aplicação.

### Repositories

Realizam o acesso e a persistência das informações no banco de dados, isolando as operações de armazenamento das demais camadas.

### Services

Concentram regras de negócio e operações como:

- análise documental;
- processamento de características;
- gerenciamento de imagens;
- Controle Técnico;
- versionamento;
- preparação do relatório;
- geração e exportação de documentos.

### UI

Contém a interface gráfica desenvolvida em PySide6, incluindo páginas, componentes reutilizáveis e ferramentas de edição.

### Report Engine

Responsável pela geração dos documentos PDF.

O motor utiliza componentes compartilhados e renderizadores específicos para cada template, permitindo manter uma identidade visual comum sem impedir que cada tipo de inspeção possua sua própria estrutura técnica.

---

## Tecnologias utilizadas

O projeto utiliza principalmente:

- **Python** — linguagem principal;
- **PySide6** — desenvolvimento da interface desktop;
- **SQLite** — persistência local;
- **PyMuPDF / Fitz** — leitura, processamento e geração de PDFs;
- **Matplotlib** — geração de gráficos;
- **Git** — controle de versão;
- **GitHub** — armazenamento e histórico do código-fonte.

As dependências necessárias para execução estão listadas em:

```text
requirements.txt
```

---

## Banco de dados

O METRA utiliza atualmente um banco de dados **SQLite local**.

Entre as informações persistidas estão:

- processos;
- documentos;
- extrações;
- características;
- informações de medição;
- imagens;
- marcações;
- Controle Técnico;
- versões de relatório;
- informações de rastreabilidade.

Arquivos locais utilizados durante desenvolvimento e testes não devem ser enviados ao repositório quando contiverem dados específicos dos processos utilizados para validação.

---

## Como executar

### 1. Clonar o repositório

```bash
git clone https://github.com/Anaju-h/METRA-Relatorios.git
```

### 2. Entrar na pasta

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

```powershell
.venv\Scripts\Activate.ps1
```

### 5. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 6. Executar

```bash
python app.py
```

---

## Estrutura de documentação

A documentação complementar do projeto está organizada no diretório:

```text
docs/
```

A entrega final será organizada com materiais como:

```text
docs/
│
├── documentacao_tecnica/
│   └── Documentacao_Tecnica_METRA.pdf
│
├── manual/
│   └── Manual_de_Utilizacao_METRA.pdf
│
├── apresentacao/
│   └── Apresentacao_METRA.pdf
│
└── ...
```

Documentos internos de desenvolvimento e registros dos checkpoints também podem permanecer no diretório como histórico do projeto.

---

## Demonstração

Para a demonstração prática, o METRA pode utilizar um relatório de medição real como documento de origem.

O fluxo de demonstração pode apresentar:

1. importação do relatório original;
2. análise automática;
3. informações e características identificadas;
4. imagens e marcações;
5. informações de medição;
6. Controle Técnico;
7. preparação do relatório;
8. seleção das seções;
9. pré-visualização;
10. exportação do relatório consolidado.

Documentos reais que contenham informações confidenciais ou dados de clientes não devem ser publicados em repositórios públicos sem a devida autorização ou anonimização.

---

## Status do projeto

**Fase de finalização, validação e preparação da entrega.**

O fluxo principal da aplicação, os templates de relatório, o Controle Técnico, o versionamento e os mecanismos de rastreabilidade encontram-se implementados.

As atividades finais estão concentradas em:

- testes integrados;
- validação dos fluxos completos;
- documentação técnica;
- manual de utilização;
- preparação da demonstração;
- preparação da distribuição da aplicação.

---

## Documentação

A documentação complementar está disponível em [`docs/`](docs/).

O diretório reúne materiais relacionados a:

- desenvolvimento;
- arquitetura;
- banco de dados;
- checkpoints;
- documentação técnica;
- manual de utilização;
- testes;
- materiais de apresentação.

---

## Desenvolvimento

O METRA foi desenvolvido como uma solução para apoiar a automação e a melhoria do processo de preparação de relatórios técnicos de metrologia.

A proposta combina **automação, organização, análise técnica, padronização, rastreabilidade e validação humana** em um único fluxo de trabalho.