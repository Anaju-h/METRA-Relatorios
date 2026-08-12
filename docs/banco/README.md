# Banco de Dados do METRA

O METRA utiliza atualmente **SQLite** como mecanismo de persistência local.

O banco armazena as informações estruturadas necessárias para que os processos possam ser criados, editados, fechados e posteriormente reabertos sem perda das informações registradas.

Os arquivos físicos, como PDFs e imagens, permanecem no sistema de arquivos. O banco mantém os registros necessários para relacioná-los aos respectivos processos.

---

# Visão geral

O processo é a entidade central da estrutura de dados.

De forma simplificada:

```text
                         PROJECT
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
      DOCUMENTS         MEASUREMENT         IMAGES
          │                                   │
          ▼                                   ▼
     EXTRACTIONS                          ANNOTATIONS
          │
          ▼
   CHARACTERISTICS

          PROJECT
             │
             ├──────── TECHNICAL CONTROL
             │
             └──────── REPORT VERSIONS
```

Essa estrutura permite reunir em um mesmo processo os documentos de origem, dados extraídos, características, informações de medição, evidências visuais, controle técnico e histórico de relatórios.

---

# Principais entidades

## Projects

Representa um processo criado no METRA.

Entre as informações associadas ao processo estão:

- identificador do relatório;
- nome;
- template;
- tipo de inspeção;
- modo de análise;
- quantidade;
- tecnologia;
- versão do template;
- cliente;
- peça;
- código da peça;
- equipamento;
- descrição;
- situação;
- versão;
- data de criação;
- data de atualização.

O identificador do relatório segue o padrão utilizado pelo METRA, por exemplo:

```text
MET-2026-0006
```

---

## Project Documents

Representa os documentos PDF vinculados ao processo.

Um processo pode possuir vários documentos.

Entre as informações mantidas estão:

- processo relacionado;
- caminho do arquivo;
- nome original;
- nome armazenado;
- identificador da unidade ou amostra;
- ordem do documento;
- situação da análise;
- mensagem de processamento;
- origem identificada;
- quantidade de páginas.

Essa estrutura permite trabalhar tanto com peça única quanto com conjuntos de relatórios pertencentes a um lote.

---

## Report Extractions

Armazena informações identificadas durante a análise dos relatórios.

A extração pode estar associada ao processo e ao documento que originou os dados.

Entre os dados que podem ser identificados estão:

- nome da peça;
- máquina;
- número da máquina;
- operador;
- número da peça;
- data e horário da medição;
- quantidade de medições;
- quantidade fora de tolerância;
- duração;
- software;
- versão do software;
- quantidade de páginas;
- tipo de análise;
- alinhamento;
- situação da revisão.

A informação extraída automaticamente permanece sujeita à validação do usuário.

---

## Characteristics

Representa as características técnicas identificadas nos documentos de medição.

Esses registros permitem que o METRA consolide resultados e utilize as informações posteriormente na geração do relatório.

Em processos em lote, características equivalentes provenientes de diferentes documentos podem ser utilizadas para análises consolidadas e estatísticas.

---

## Measurements

Armazena informações relacionadas à execução da medição.

Entre os campos utilizados estão informações como:

- responsável pela medição;
- data e horário;
- referência de desenho;
- alinhamento;
- fixação;
- detalhes da máquina;
- acessórios;
- sensores;
- instruções especiais.

Esses dados complementam as informações extraídas automaticamente dos relatórios.

---

## Project Images

Representa as imagens adicionadas ao processo.

As imagens podem ser utilizadas como:

- fotografias;
- CAD;
- renderizações;
- evidências técnicas.

Entre os dados registrados estão:

- caminho do arquivo;
- nome;
- tipo;
- legenda;
- posição;
- indicação de imagem principal.

---

## Annotations

Armazena as marcações criadas sobre as imagens do processo.

Podem representar recursos como:

- retângulos;
- círculos;
- textos;
- identificadores;
- marcações numeradas.

As coordenadas e propriedades necessárias para reconstruir a anotação são mantidas no banco.

---

## Technical Controls

Armazena as informações relacionadas à elaboração, revisão e aprovação técnica.

Entre os registros estão:

- responsável pela elaboração;
- data de elaboração;
- responsável pela revisão;
- data da revisão;
- situação;
- observações da revisão.

Esse controle faz parte do fluxo de emissão do relatório.

Alterações relevantes realizadas após uma aprovação podem invalidar a aprovação anterior, garantindo que o relatório seja novamente revisado.

---

## Report Versions

Mantém o histórico das versões emitidas pelo sistema.

O versionamento permite preservar a rastreabilidade dos relatórios já gerados e diferenciar novas revisões do processo.

Exemplo conceitual:

```text
V1.0
  ↓
alteração
  ↓
V1.1
  ↓
nova alteração
  ↓
V1.2
```

O histórico de emissão não deve ser confundido com o estado atual de edição do processo.

---

# Relacionamentos

De forma simplificada:

```text
PROJECT
│
├── 1 : N ── PROJECT_DOCUMENTS
│              │
│              └── REPORT_EXTRACTIONS
│
├── 1 : N ── CHARACTERISTICS
│
├── 1 : 1 ── MEASUREMENTS
│
├── 1 : N ── PROJECT_IMAGES
│              │
│              └── 1 : N ── ANNOTATIONS
│
├── 1 : 1 ── TECHNICAL_CONTROLS
│
└── 1 : N ── REPORT_VERSIONS
```

A estrutura pode evoluir conforme novas necessidades forem incorporadas ao sistema.

---

# Persistência de arquivos

O SQLite não é utilizado para armazenar diretamente os PDFs e imagens em formato binário.

Esses arquivos permanecem nos diretórios dos processos.

O banco registra informações que permitem localizar e relacionar os arquivos.

Essa decisão mantém separadas:

```text
Informações estruturadas → SQLite

Arquivos físicos → Sistema de arquivos
```

---

# Exclusão e rastreabilidade

Em operações nas quais a rastreabilidade é importante, a remoção de um elemento não precisa representar necessariamente a destruição imediata do registro histórico.

Documentos retirados de um processo, por exemplo, podem deixar de participar dos cálculos e da geração do relatório sem que a existência anterior do registro seja perdida.

Esse comportamento permite preservar o histórico das operações relevantes.

---

# Situação dos processos

Os processos possuem uma situação utilizada para representar seu estado operacional.

Os principais estados atualmente utilizados são:

```text
Em edição
Concluído
```

Um processo concluído pode posteriormente ser reaberto caso seja necessária uma revisão.

A conclusão representa o encerramento operacional do trabalho naquele momento, enquanto o histórico de versões preserva as emissões anteriores.

---

# Banco local e Git

O banco utilizado durante a execução do METRA é local.

Por esse motivo, arquivos como:

```text
*.db
*.sqlite
*.sqlite3
```

não fazem parte do código-fonte versionado no repositório.

O banco necessário para execução da aplicação pode ser preparado pela própria estrutura do projeto.

Isso evita que dados de testes ou informações provenientes de processos reais sejam enviados ao Git.

---

## Estado atual

A utilização do SQLite atende ao estágio atual do METRA como aplicação desktop.

A arquitetura de persistência foi separada por meio dos repositórios, permitindo que uma futura evolução da infraestrutura de dados seja realizada com menor impacto sobre a interface e as regras de negócio.