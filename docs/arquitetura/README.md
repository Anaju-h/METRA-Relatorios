# Arquitetura do METRA

Esta documentação apresenta a organização arquitetural do **METRA — Sistema Inteligente de Pós-processamento de Relatórios Técnicos de Metrologia**.

A aplicação foi estruturada de forma modular, separando interface, regras de negócio, persistência, análise documental e geração de relatórios.

Essa separação facilita a manutenção do sistema e permite que novas funcionalidades, formatos de relatório e regras de processamento sejam incorporados sem concentrar toda a lógica em um único módulo.

---

## Visão geral

A arquitetura atual pode ser representada de forma simplificada pelo seguinte fluxo:

```text
┌─────────────────────────────────────────┐
│             INTERFACE — UI              │
│        PySide6 / páginas / componentes  │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│               SERVICES                  │
│      Regras de negócio e automações     │
├───────────────────┬─────────────────────┤
│ Análise documental│ Geração de relatório│
│ document_analysis │    report_engine    │
└─────────┬─────────┴──────────┬──────────┘
          │                    │
          ▼                    ▼
┌─────────────────────────────────────────┐
│             REPOSITORIES                │
│       Persistência e acesso a dados     │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│                SQLITE                   │
│          Banco de dados local           │
└─────────────────────────────────────────┘
```

Além do banco de dados, o METRA utiliza o sistema de arquivos para armazenar documentos originais, imagens, arquivos gerados, previews e demais recursos associados aos processos.

---

# Estrutura principal

A organização principal do código é:

```text
METROREPORT/
│
├── assets/
├── database/
├── models/
├── repositories/
├── services/
├── ui/
├── utils/
│
├── app.py
├── requirements.txt
└── README.md
```

Cada área possui uma responsabilidade específica.

---

## `app.py`

É o ponto de entrada da aplicação.

Sua função é inicializar os recursos necessários para execução do METRA e iniciar a interface gráfica.

---

# Camada de interface

```text
ui/
├── components/
├── editor/
├── pages/
└── main_window.py
```

A camada `ui` contém os elementos visuais e a navegação da aplicação.

O sistema utiliza **PySide6**, baseado no framework Qt.

## `main_window.py`

A janela principal coordena:

- cabeçalho institucional;
- menu lateral;
- navegação entre páginas;
- processo atualmente aberto;
- integração entre as páginas e os serviços da aplicação.

## `components/`

Contém componentes reutilizáveis da interface, como:

- cabeçalho da aplicação;
- menu lateral;
- cabeçalhos internos;
- cards;
- indicadores;
- visualizador de PDF;
- gráfico de situação dos processos.

A utilização de componentes evita repetição e ajuda a manter consistência visual.

## `pages/`

Contém as páginas funcionais do METRA.

Entre elas estão:

- Home;
- Processos;
- Novo Processo;
- Visão Geral;
- Documentos;
- Características;
- Medição;
- Imagens;
- Controle Técnico;
- Relatório Final;
- Pré-visualização do relatório.

O fluxo de criação de um processo também possui componentes próprios dentro de:

```text
ui/pages/new_project/
```

Essa estrutura divide a criação em diferentes etapas e evita concentrar todo o processo em uma única tela.

## `editor/`

Contém os recursos relacionados à edição e marcação de imagens.

Essa área permite trabalhar com evidências visuais utilizadas posteriormente na documentação técnica.

---

# Camada de serviços

```text
services/
```

A camada de serviços concentra grande parte das regras de negócio do METRA.

Ela atua como intermediária entre a interface, os mecanismos de análise, os repositórios e a geração dos documentos.

Entre suas responsabilidades estão:

- gerenciamento dos processos;
- documentos;
- características;
- informações de medição;
- imagens;
- marcações;
- controle técnico;
- análise de lotes;
- extração de relatórios;
- estatísticas;
- geração do relatório final;
- versionamento;
- rastreabilidade.

---

# Motor de análise documental

```text
services/document_analysis/
```

Esse módulo é responsável por interpretar os documentos importados para o METRA.

Sua estrutura foi separada em componentes especializados para permitir a evolução do mecanismo de extração.

Entre suas responsabilidades estão:

- leitura do PDF;
- identificação da origem do documento;
- identificação de perfis conhecidos;
- localização de informações;
- interpretação de linhas e tabelas;
- consolidação dos resultados;
- validação dos dados extraídos.

A arquitetura permite trabalhar com diferentes estruturas documentais por meio de perfis e interpretadores específicos.

Atualmente existem estruturas voltadas para fontes como:

- CALYPSO;
- ZEISS INSPECT.

A extração automática não elimina a validação humana. Os dados identificados pelo sistema podem ser revisados antes de serem utilizados no processo.

---

# Motor de geração de relatórios

```text
services/report_engine/
```

O `report_engine` é responsável pela construção dos relatórios técnicos produzidos pelo METRA.

A geração foi separada do restante da aplicação para permitir layouts diferentes conforme o tipo de inspeção.

Sua estrutura inclui:

```text
report_engine/
├── components/
├── renderers/
├── base_renderer.py
├── layout_engine.py
├── report_context.py
└── template_registry.py
```

## Componentes

Elementos reutilizáveis dos relatórios, como:

- cabeçalho institucional;
- rodapé;
- seções.

## Renderizadores

Cada família de relatório pode possuir seu próprio renderizador.

Atualmente a estrutura contempla:

```text
renderers/
├── custom/
├── dimensional_batch/
├── dimensional_individual/
└── tomography/
```

Isso permite que uma inspeção dimensional em lote, por exemplo, utilize uma organização diferente de um relatório de tomografia.

---

# Models

```text
models/
```

Os modelos representam as principais entidades utilizadas pelo sistema.

Entre elas:

- processo;
- documento;
- extração;
- característica;
- medição;
- imagem;
- marcação;
- controle técnico;
- versão de relatório.

Os modelos transportam os dados entre as diferentes camadas da aplicação.

---

# Repositories

```text
repositories/
```

Os repositórios concentram as operações de persistência.

Essa camada evita que comandos de banco de dados sejam espalhados pelas páginas da interface ou pelas regras de negócio.

O fluxo esperado é:

```text
Interface
   ↓
Service
   ↓
Repository
   ↓
SQLite
```

---

# Banco de dados

```text
database/
```

Essa área contém os recursos responsáveis pela conexão e preparação do banco SQLite.

O banco é utilizado para armazenar as informações estruturadas dos processos e garantir que um trabalho possa ser fechado e posteriormente reaberto.

A estrutura detalhada é documentada separadamente em:

```text
docs/banco-de-dados/
```

---

# Sistema de arquivos

Nem todos os elementos manipulados pelo METRA são armazenados diretamente no SQLite.

Cada processo possui uma estrutura própria de arquivos, permitindo separar documentos originais, imagens e resultados gerados.

Exemplo conceitual:

```text
projects/
└── MET-AAAA-NNNN/
    ├── original/
    ├── images/
    ├── attachments/
    ├── generated/
    ├── previews/
    ├── exports/
    └── cache/
```

Esses diretórios representam dados locais de execução e não fazem parte do código-fonte versionado no Git.

---

# Princípios utilizados

A arquitetura do METRA busca seguir alguns princípios principais:

### Separação de responsabilidades

Interface, regras de negócio, persistência, análise e geração de relatórios possuem responsabilidades diferentes.

### Modularidade

Funcionalidades específicas são divididas em módulos menores.

### Reutilização

Componentes visuais e componentes dos relatórios podem ser reutilizados em diferentes partes do sistema.

### Rastreabilidade

Alterações importantes e emissões de relatórios podem ser registradas e associadas ao processo.

### Validação humana

A automação auxilia o trabalho técnico, mas informações extraídas automaticamente continuam sujeitas à revisão do usuário.

### Evolução

A estrutura permite incorporar novos tipos de inspeção, equipamentos, documentos e templates sem reconstruir toda a aplicação.

---

## Estado atual

A arquitetura apresentada representa a estrutura atual do METRA durante sua fase de desenvolvimento e refinamento.

Ela poderá receber ajustes conforme os testes finais e as necessidades identificadas durante a validação do sistema.