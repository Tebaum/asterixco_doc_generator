# Asterixco Infrastructure Doc Generator (CrewAI)

Sistema multi-agente desenvolvido em **Python** e **CrewAI** para automatizar a geração de documentação técnica de infraestrutura de TI, redes e segurança eletrônica a partir de planilhas de inventário e capturas de tela (prints de configuração).

## Arquitetura
- **Analista de Levantamento de Infraestrutura:** Extrai e consolida dados de planilhas (`.xlsx`/`.csv`) e screenshots técnicos via ferramenta customizada (`LeitorPrintsTool`) com sanitização automática de dados sensíveis.
- **Engenheiro de Documentação Técnica:** Estrutura o relatório final em Markdown padronizado em 5 seções (Visão Geral, Topologia e Rede, Segurança Eletrônica, Servidores/Serviços e Lacunas).

## Como executar
1. Clone o repositório e crie o ambiente virtual.
2. Copie `.env.example` para `.env` e preencha suas variáveis.
3. Coloque as evidências na pasta `entradas/prints/` e execute `crewai run`.