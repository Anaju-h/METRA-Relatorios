# Fluxo do Sistema — METRA

O METRA foi desenvolvido para organizar o pós-processamento de relatórios técnicos de metrologia em um fluxo único.

O objetivo é reduzir atividades manuais e repetitivas sem retirar do usuário a responsabilidade pela revisão e validação técnica das informações.

---

# Fluxo geral

O funcionamento principal pode ser representado da seguinte forma:

```text
INÍCIO
  │
  ▼
NOVO PROCESSO
  │
  ├───────────────┐
  │               │
  ▼               ▼
IMPORTAR PDFs   PROCESSO MANUAL
  │               │
  ▼               │
ANÁLISE            │
AUTOMÁTICA          │
  │               │
  ▼               │
REVISÃO             │
DA EXTRAÇÃO         │
  │               │
  └───────┬───────┘
          ▼
   CRIAÇÃO DO PROCESSO
          │
          ▼
      VISÃO GERAL
          │
          ▼
      DOCUMENTOS
          │
          ▼
    CARACTERÍSTICAS
          │
          ▼
        MEDIÇÃO
          │
          ▼
        IMAGENS
          │
          ▼
   CONTROLE TÉCNICO
          │
          ▼
    RELATÓRIO FINAL
          │
          ▼
   PRÉ-VISUALIZAÇÃO
          │
          ▼
  APROVAÇÃO E EXPORTAÇÃO
          │
          ▼
     VERSIONAMENTO
          │
          ▼
       CONCLUSÃO
```

---

# 1. Início

A Home apresenta uma visão geral dos processos existentes e permite iniciar um novo trabalho ou abrir um processo já criado.

Também apresenta informações resumidas sobre a situação dos processos.

---

# 2. Central de Processos

A página de Processos funciona como central de gerenciamento dos trabalhos existentes.

Ela permite consultar processos em diferentes situações, pesquisar registros e abrir um processo para continuar o trabalho.

Um novo processo também pode ser iniciado a partir dessa área.

---

# 3. Criação de um novo processo

Ao iniciar um processo, o usuário pode seguir diferentes caminhos.

## Processo com documentos

O usuário importa um ou vários relatórios PDF.

Essa modalidade permite que o METRA analise os documentos antes da criação definitiva do processo.

## Processo manual

O usuário pode criar o processo sem depender de um relatório de origem reconhecido pelo mecanismo automático.

Isso permite utilizar o sistema mesmo quando não existe um documento compatível com os analisadores disponíveis.

---

# 4. Importação dos documentos

O sistema aceita a inclusão de documentos que serão utilizados como origem das informações do processo.

Quando vários relatórios pertencem ao mesmo conjunto de peças, eles podem formar um processo em lote.

Cada documento permanece individualmente identificado mesmo quando participa de uma análise consolidada.

---

# 5. Análise automática

Após a importação, o mecanismo de análise documental tenta identificar informações relevantes.

Entre elas podem estar:

- origem do relatório;
- peça;
- identificador da unidade;
- equipamento;
- operador;
- data de medição;
- software;
- características;
- resultados;
- quantidade de medições.

A quantidade de documentos e os identificadores encontrados também podem auxiliar na determinação do contexto do processo.

---

# 6. Revisão da extração

As informações identificadas automaticamente são apresentadas para revisão.

Essa etapa é importante porque o METRA utiliza automação como apoio, e não como substituição da validação técnica.

Quando necessário, o usuário pode complementar ou corrigir as informações antes de continuar.

---

# 7. Criação definitiva

Depois da análise e revisão, o processo é criado.

O sistema atribui um identificador próprio, como:

```text
MET-2026-0006
```

A partir desse momento, as diferentes informações passam a fazer parte de um mesmo processo rastreável.

---

# 8. Visão Geral

A Visão Geral funciona como painel do processo.

Ela apresenta informações como:

- quantidade de documentos;
- características;
- imagens;
- pendências;
- tipo de inspeção;
- modo de análise;
- template;
- tecnologia;
- equipamento;
- identificação da peça;
- situação;
- andamento do processo.

Essa página permite verificar rapidamente o estado do trabalho.

---

# 9. Documentos

A área de Documentos apresenta os relatórios originais vinculados ao processo.

Cada documento mantém informações próprias, como:

- nome;
- origem;
- quantidade de páginas;
- identificação;
- peça;
- equipamento;
- características encontradas;
- situação da análise.

O usuário pode consultar os documentos individualmente.

Também é possível adicionar novos documentos ao processo.

Quando um documento deixa de participar do processo, sua remoção deve preservar a rastreabilidade necessária.

---

# 10. Características

A página de Características reúne os resultados identificados nos relatórios.

Ela permite analisar as informações que serão utilizadas posteriormente no relatório final.

Em processos com várias unidades, os dados podem ser consolidados para permitir análises estatísticas do lote.

---

# 11. Medição

A área de Medição reúne informações complementares relacionadas à execução da inspeção.

Entre elas podem estar:

- responsável pela medição;
- data;
- desenho de referência;
- alinhamento;
- fixação;
- equipamento;
- acessórios;
- sensores;
- instruções especiais.

Parte das informações pode ser obtida automaticamente, enquanto outras dependem do preenchimento ou validação do usuário.

---

# 12. Imagens

A página de Imagens permite adicionar evidências visuais ao processo.

As imagens podem representar:

- fotografias;
- modelos CAD;
- renderizações;
- evidências técnicas.

Também podem receber:

- legenda;
- classificação;
- ordenação;
- marcações.

---

# 13. Marcações

O editor de imagens permite destacar regiões importantes das evidências.

Entre os recursos disponíveis podem estar:

- retângulos;
- círculos;
- textos;
- numeração;
- outros elementos de identificação.

Essas informações podem posteriormente fazer parte do relatório técnico.

---

# 14. Controle Técnico

Antes da emissão definitiva, o processo passa pelo controle técnico.

Essa área registra informações relacionadas à elaboração e revisão do relatório.

O fluxo busca garantir que alterações relevantes realizadas após uma aprovação invalidem a aprovação anterior.

De forma simplificada:

```text
PROCESSO REVISADO
       │
       ▼
    APROVADO
       │
       ▼
ALTERAÇÃO RELEVANTE?
   │            │
  NÃO          SIM
   │            │
   ▼            ▼
MANTÉM      APROVAÇÃO
ESTADO      INVALIDADA
                │
                ▼
          NOVA REVISÃO
```

---

# 15. Relatório Final

A página de Relatório Final consolida as informações que serão utilizadas na geração do documento.

O conteúdo varia conforme o template selecionado.

O METRA possui estruturas específicas para diferentes contextos, incluindo:

- dimensional individual;
- dimensional em lote;
- tomografia;
- relatório personalizado.

---

# 16. Pré-visualização

Antes da emissão, o relatório é apresentado em uma área de pré-visualização.

Essa etapa permite verificar o documento antes da exportação definitiva.

O usuário pode retornar ao processo para corrigir informações caso identifique algum problema.

---

# 17. Aprovação e exportação

Após a conferência, o relatório pode ser aprovado e exportado.

A emissão definitiva registra a versão correspondente no histórico do processo.

---

# 18. Versionamento

O METRA mantém histórico das emissões realizadas.

Exemplo:

```text
Primeira emissão
      │
      ▼
     V1.0
      │
      ▼
Alteração posterior
      │
      ▼
Nova revisão / aprovação
      │
      ▼
     V1.1
```

As versões anteriores permanecem registradas para preservar a rastreabilidade.

---

# 19. Conclusão

Depois que o trabalho estiver encerrado, o processo pode ser marcado como:

```text
Concluído
```

A conclusão diferencia processos em andamento daqueles cujo fluxo foi encerrado.

---

# 20. Reabertura

A conclusão não impede futuras correções.

Caso seja necessário alterar um processo concluído, ele pode ser reaberto.

O fluxo passa então a ser:

```text
CONCLUÍDO
    │
    ▼
REABRIR PROCESSO
    │
    ▼
EM EDIÇÃO
    │
    ▼
ALTERAÇÕES
    │
    ▼
REVISÃO
    │
    ▼
NOVA EMISSÃO
```

O histórico anterior permanece preservado.

---

# Rastreabilidade do fluxo

Um dos objetivos centrais do METRA é evitar que a geração do relatório seja tratada apenas como criação de um arquivo PDF.

O relatório faz parte de um processo que contém:

```text
Documentos de origem
        +
Dados extraídos
        +
Características
        +
Informações da medição
        +
Imagens e evidências
        +
Controle técnico
        +
Versões emitidas
        =
PROCESSO RASTREÁVEL
```

---

# Princípio de automação

O fluxo do METRA segue uma ideia central:

> **automatizar o que puder ser identificado pelo sistema e permitir que o usuário revise aquilo que exige validação técnica.**

Dessa forma, o sistema busca reduzir trabalho repetitivo sem remover o controle humano sobre as informações que compõem o relatório final.

---

## Estado atual

Este documento representa o fluxo funcional atual do METRA durante sua fase de desenvolvimento.

O fluxo poderá receber ajustes após os testes integrados e a validação final da aplicação.