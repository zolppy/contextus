# 🤖 Contextus — Assistente Virtual para Dados Educacionais do IFBA

![Status](https://img.shields.io/badge/Status-Finalizado-red?style=for-the-badge)
![Acesso](https://img.shields.io/badge/Acesso-Gratuito%20via%20Web-green?style=for-the-badge)

**Contextus** é parte do meu Trabalho de Conclusão de Curso de Licenciatura em Computação do Instituto Federal de Educação, Ciência e Tecnologia da Bahia, Campus Jacobina. Trata-se de um protótipo de assistente virtual inteligente que responde perguntas sobre os **indicadores educacionais** do **Instituto Federal da Bahia – Campus Jacobina**, a partir dos dados públicos da **Plataforma Nilo Peçanha (PNP)**.

> 🔍 _“Transformando dados educacionais em conhecimento acessível.”_

---

## 📑 Tabela de Conteúdos

- [Sobre o Projeto](#sobre-o-projeto)
- [Escopo e Limitações](#escopo-e-limitações)
- [Funcionalidades Principais](#funcionalidades-principais)
- [Como Acessar](#como-acessar)
- [Primeiros Passos (Exemplos de Perguntas)](#primeiros-passos-exemplos-de-perguntas)
- [Entendendo os Indicadores](#entendendo-os-indicadores)
- [Conjuntos de Dados Disponíveis](#conjuntos-de-dados-disponíveis)
- [Dúvidas Frequentes](#dúvidas-frequentes)
- [Autor e Orientação](#autor-e-orientação)
- [Licença](#licença)
- [Agradecimentos](#agradecimentos)

---

<a id="sobre-o-projeto"></a>

## 📌 Sobre o Projeto

O Contextus foi criado para apoiar **gestores, coordenadores e pesquisadores** do **IFBA – Campus Jacobina** que precisam analisar os dados de **evasão** de forma simples. Em vez de aprender uma ferramenta técnica ou escrever consultas, você faz uma pergunta em **português natural** e o assistente:

1. Interpreta sua pergunta.
2. Consulta os dados da PNP (já carregados no sistema).
3. Devolve uma resposta em texto e, quando apropriado, gera **gráficos dinâmicos**.

🌐 **Atalho para uso imediato:** acesse <a href="https://contextus.streamlit.app" target="_blank"><strong>https://contextus.streamlit.app</strong></a>.

💻 **Código-fonte:** caso tenha interesse em aspectos técnicos de implementação, o código-fonte do projeto está disponível em <a href="https://github.com/zolppy/contextus" target="_blank"><strong>https://github.com/zolppy/contextus</strong></a>.

📄 **Documentação:** Se você estiver lendo isto através do GitHub, este mesmo conteúdo (README.md) pode ser acessado em uma página web em <a href="https://zolppy.github.io/contextus" target="_blank"><strong>https://zolppy.github.io/contextus</strong></a>, hospedado via GitHub Pages. Se já estiver na página, não precisa abrir.

---

<a id="escopo-e-limitações"></a>

## 📌 Escopo e Limitações

- **O que o assistente sabe responder:** apenas perguntas relacionadas aos **dados de evasão do Campus Jacobina** do IFBA disponíveis na PNP.
- **O que ele NÃO responde:** consultas sobre outros campi, outras instituições, comparações entre IFs ou temas fora do domínio da evasão do Campus Jacobina.
- **Período dos dados:** os arquivos utilizados cobrem os anos de **2017 a 2024**, dependendo da tabela. Consulte os dicionários de dados para detalhes.
- **Indicadores disponíveis:** Concluídos, Evadidos, Retidos, Taxa de Evasão, Índice de Eficiência Acadêmica. As definições exatas estão na seção [Entendendo os Indicadores](#-entendendo-os-indicadores).

---

<a id="funcionalidades-principais"></a>

## ✨ Funcionalidades Principais

- 🧠 **Respostas em linguagem natural** – você pergunta como se estivesse conversando com um colega.
- 📊 **Gráficos automáticos** – ao comparar cursos, anos ou categorias, o assistente gera gráficos para facilitar a visualização.
- 🏫 **Foco exclusivo no Campus Jacobina** – o agente nunca inventa informações; se não souber, ele avisa.
- 📁 **Histórico de conversas** – você pode manter até 6 conversas separadas, acessar perguntas anteriores e excluí-las quando desejar.
- 🔒 **Segurança** – o sistema não armazena dados pessoais além das perguntas feitas; as chaves de acesso são protegidas.

---

<a id="como-acessar"></a>

## 🌐 Como Acessar

1. Abra o navegador e vá para <a href="https://contextus.streamlit.app" target="_blank"><strong>https://contextus.streamlit.app</strong></a>.
2. Na tela inicial, você verá uma caixa de mensagem na parte inferior.
3. Digite sua pergunta sobre os dados de evasão do Campus Jacobina e pressione **Enter**.
4. A resposta aparecerá em texto e, se houver dados comparativos, um gráfico será exibido automaticamente.

**Dica:** Use a barra lateral para iniciar uma **nova conversa** ou acessar conversas anteriores.

---

<a id="primeiros-passos-exemplos-de-perguntas"></a>

## 🧭 Primeiros Passos (Exemplos de Perguntas)

Experimente perguntas como estas:

- _“Qual a taxa de evasão do Campus Jacobina em 2024?”_
- _“Quantos alunos evadiram do curso Técnico em Informática no último ano?”_
- _“Evolução anual do número de concluintes desde 2017.”_
- _“Comparar a evasão entre cursos integrados e subsequentes.”_
- _“Qual curso teve a maior taxa de evasão em 2023?”_
- _“Mostre um gráfico do número de evasões por curso desde 2017.”_
- _“Quantos alunos evadiram do curso Técnico em Mineração no ano de 2020?”_
- _“Qual a evolução do índice de eficiência acadêmica do Campus Jacobina de 2017 a 2024?”_
- _“Quantos alunos estavam com matrícula ativa (em curso) em 2024?”_
- _“Qual a taxa de evasão dos cursos subsequentes em 2023?”_

Se o assistente não puder responder, ele indicará claramente que os dados não estão disponíveis ou que a pergunta está fora do escopo.

---

<a id="entendendo-os-indicadores"></a>

## 📊 Entendendo os Indicadores

- **Concluídos (Eficiência Acadêmica | Concluídos):** número de alunos que concluíram o curso no ciclo de referência.
- **Concluídos %:** percentual de concluintes em relação às matrículas dos ciclos concluídos no ano anterior.
- **Índice de Eficiência Acadêmica %:** medida composta que combina o percentual de concluintes com uma projeção dos retidos que ainda podem concluir.
- **Número de Evadidos:** alunos que abandonaram, foram desligados, transferidos ou reprovados no período.
- **Retidos:** alunos que ultrapassaram o prazo previsto para conclusão, mas ainda estão matriculados.
- **Taxa de Evasão %:** percentual de evadidos em relação ao total de matrículas dos ciclos concluídos no ano anterior.

Para definições mais detalhadas, consulte os dicionários de dados disponíveis na Plataforma Nilo Peçanha.

---

<a id="conjuntos-de-dados-disponíveis"></a>

## 📂 Conjuntos de Dados Disponíveis

O Contextus organiza os indicadores da Plataforma Nilo Peçanha em **três grandes grupos** (tabelas), todos filtrados exclusivamente para o Campus Jacobina. Entender o que cada grupo contém ajuda a formular perguntas ainda mais úteis.

### 1. Indicadores Anuais de Eficiência Acadêmica

- **O que traz:** visão geral do campus, ano a ano, com totais de concluintes, evadidos, retidos e as respectivas taxas.
- **Principais informações disponíveis:**
  - `Eficiência Acadêmica | Concluídos` e `Concluídos %`
  - `Número de Evadidos` e `Taxa de Evasão %`
  - `Retidos` e `Retidos %`
  - `Índice de Eficiência Acadêmica %`
- **Pergunta típica:** _“Qual a taxa de evasão do Campus Jacobina em 2024?”_

### 2. Taxa de Evasão por Curso

- **O que traz:** dados de evasão detalhados por curso, turno, tipo de oferta e modalidade de ensino.
- **Principais informações disponíveis:**
  - `nomeCurso` (ex.: Técnico em Informática, Computação)
  - `tipoOferta` (Integrado, Subsequente, PROEJA etc.)
  - `turnoCurso` e `ModalidadeEnsino`
  - `Número de Matrículas`, `Matrículas | Número de Evadidos` e `Matrículas | Taxa de Evasão %`
- **Perguntas típicas:** _“Qual curso teve a maior evasão em 2023?”_, _“Comparar evasão entre cursos integrados e subsequentes.”_

### 3. Situação de Matrícula

- **O que traz:** o detalhamento de cada matrícula (concluinte, em curso ou evadido) e o motivo da evasão.
- **Principais informações disponíveis:**
  - `categoriaSituacao` (Concluintes, Em curso, Evadidos)
  - `nomeSituacao` (Abandono, Desligada, Concluída, Integralizada etc.)
  - `FluxoRetido` (indica se o aluno ultrapassou o prazo regular)
  - `Número de Matrículas`
- **Perguntas típicas:** _“Quantos alunos abandonaram o curso em 2024?”_, _“Quantos estavam com matrícula ativa em 2023?”_

> 💡 **Lembre‑se:** todas as tabelas cobrem aproximadamente os anos de **2017 a 2024** e referem‑se apenas ao **Campus Jacobina**. O assistente se baseia nelas para responder suas dúvidas.

---

<a id="dúvidas-frequentes"></a>

## ❓ Dúvidas Frequentes

**1. Preciso instalar alguma coisa?**
Não. O Contextus está disponível online e pode ser usado diretamente pelo navegador.

**2. Posso perguntar sobre outros campi do IFBA?**
No momento, o assistente está limitado aos dados do **Campus Jacobina**.

**3. Os dados são atualizados automaticamente?**
Os dados carregados refletem as versões dos arquivos fornecidos pela PNP até 2024. Novas edições podem ser incorporadas futuramente.

**4. Minhas conversas ficam salvas?**
Sim, até 6 conversas ficam armazenadas no seu navegador (vinculadas ao dispositivo que você está usando). Você pode excluí‑las a qualquer momento.

**5. O que fazer se a resposta não fizer sentido?**
Tente reformular a pergunta com termos mais diretos (ex.: “taxa de evasão por curso em 2023”). Se o problema persistir, entre em contato com o desenvolvedor através do e-mail <a href="mailto:zolppy.me@gmail.com" target="_blank"><strong>zolppy.me@gmail.com</strong></a>.

---

<a id="autor-e-orientação"></a>

## 👨‍🎓 Autor e Orientação

- **Desenvolvedor:** Gabriel Cavalcante de Jesus Oliveira
- **Curso:** Licenciatura em Computação
- **Instituição:** Instituto Federal da Bahia – Campus Jacobina
- **Orientador(a):** Prof. Me. Ivo Chaves de França

---

<a id="licença"></a>

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT** – veja o arquivo [LICENSE](LICENSE) para detalhes.

---

<a id="agradecimentos"></a>

## 🙏 Agradecimentos

- À **Plataforma Nilo Peçanha** por disponibilizar os dados públicos da Rede Federal.
- Ao **IFBA Campus Jacobina** pelo suporte e formação.
- Ao orientador **Prof. Me. Ivo Chaves de França**.
- À comunidade open‑source pelas ferramentas que tornaram este projeto possível.
