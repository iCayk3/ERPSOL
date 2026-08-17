# Continuidade do projeto — ERP de Provedor SOL

## Objetivo do produto

Transformar o ERPNext/Frappe em um ERP próprio para provedores de internet. O ERPNext é usado como base técnica porque já possui financeiro, clientes, contratos, estoque, ativos, usuários e permissões, mas o produto final deve ter identidade, fluxos e organização próprios da SOL.

Não tratar o trabalho apenas como uma extensão genérica do ERPNext. As decisões de interface e domínio devem priorizar a operação de um ISP.

## Ambiente de desenvolvimento

- Sistema operacional: Windows
- Docker Desktop instalado e funcionando
- URL do site: `http://development.localhost:8000`
- Usuário inicial: `Administrator`
- Senha atual do ambiente local: `admin`
- Site Frappe: `development.localhost`
- Frappe: versão 16
- ERPNext: versão 16

### Caminhos importantes

- Repositório principal:
  `C:\Users\SOL NOC\Documents\Dev\Projetos\erpnext-develop`
- Docker:
  `C:\Users\SOL NOC\Documents\Dev\Projetos\erpnext-develop\frappe_docker`
- Bench:
  `C:\Users\SOL NOC\Documents\Dev\Projetos\erpnext-develop\frappe_docker\development\frappe-bench`
- App personalizado:
  `C:\Users\SOL NOC\Documents\Dev\Projetos\erpnext-develop\frappe_docker\development\frappe-bench\apps\sol_brasil`
- Executável do Docker:
  `C:\Users\SOL NOC\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe`
- Compose:
  `devcontainer-example\docker-compose.yml`

### Comandos frequentes

Executar a partir da pasta `frappe_docker`:

```powershell
& 'C:\Users\SOL NOC\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe' compose -f devcontainer-example\docker-compose.yml ps
```

Limpar cache:

```powershell
& 'C:\Users\SOL NOC\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe' compose -f devcontainer-example\docker-compose.yml exec -T frappe bash -lc 'cd /workspace/development/frappe-bench && bench --site development.localhost clear-cache'
```

Aplicar campos personalizados do app:

```powershell
& 'C:\Users\SOL NOC\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe' compose -f devcontainer-example\docker-compose.yml exec -T frappe bash -lc 'cd /workspace/development/frappe-bench && bench --site development.localhost execute sol_brasil.install.setup_customer_fields && bench --site development.localhost clear-cache'
```

Migração completa:

```powershell
& 'C:\Users\SOL NOC\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe' compose -f devcontainer-example\docker-compose.yml exec -T frappe bash -lc 'cd /workspace/development/frappe-bench && bench --site development.localhost migrate'
```

Compilar app e traduções:

```powershell
& 'C:\Users\SOL NOC\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe' compose -f devcontainer-example\docker-compose.yml exec -T frappe bash -lc 'cd /workspace/development/frappe-bench && bench build --app sol_brasil && bench --site development.localhost clear-cache'
```

Se um novo endpoint Python não for encontrado pelo processo web, reiniciar somente o Frappe:

```powershell
& 'C:\Users\SOL NOC\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe' compose -f devcontainer-example\docker-compose.yml restart frappe
```

Após mudanças de front, atualizar o navegador com `Ctrl + Shift + R`.

## Decisões de navegação e interface

- Atalhos do produto ficam na tela inicial de aplicativos/workspaces.
- Itens relacionados devem ser agrupados para não poluir a tela.
- Clientes não devem ser apresentados como subordinados conceitualmente ao módulo Vendas.
- A lista de clientes é a entrada principal.
- Ao clicar em um cliente, a ficha dele centraliza contratos, financeiro, provedor e atendimentos.
- Ao criar contrato, fatura, recebimento, chamado, ordem de serviço ou equipamento a partir da ficha, o sistema deve retornar para a ficha do cliente após concluir.
- Documentos submetíveis, como fatura e recebimento, retornam somente depois de `Enviar`, não ao salvar o rascunho.
- Manter o design nativo do Frappe: não foram feitas alterações em fontes, CSS, tamanhos ou estrutura visual global.

## Workspaces e atalhos

Implementados em `sol_brasil/workspace.py`.

Grupos principais:

- SOL Provedor
- Clientes
- Contratos
- Planos
- Financeiro
- Atendimento
- Rede e equipamentos
- Estoque
- Relatórios
- Configurações

Atalhos de clientes incluem:

- Listagem de clientes definitivos
- Cadastro completo
- Cadastro resumido (Lead)
- Futuros clientes (Leads)

## Clientes e Leads

### Cadastro completo

- Cria diretamente um `Customer`.
- CPF é obrigatório para pessoa física.
- CNPJ é obrigatório para pessoa jurídica.
- Validação matemática de CPF/CNPJ.
- Bloqueio de documento duplicado.
- CPF/CNPJ, RG ou IE e nascimento ficam em Detalhes.
- Informações fiscais devem reutilizar esses dados, evitando duplicidade.

### Cadastro resumido

- O Quick Entry de Customer foi substituído para criar um `Lead`.
- CPF/CNPJ não é obrigatório no cadastro resumido.
- É obrigatório informar ao menos celular ou e-mail.
- Leads ficam em lista separada e nunca misturados aos clientes definitivos.

Arquivos principais:

- `sol_brasil/install.py`
- `sol_brasil/customer.py`
- `sol_brasil/lead.py`
- `sol_brasil/public/js/customer_quick_entry.js`
- `sol_brasil/public/js/customer_list.js`
- `sol_brasil/public/js/lead.js`

## Conversão de Lead e contratos preliminares

Criados os DocTypes:

- `Contrato Preliminar`
- `Configurações do Provedor`

Pastas:

- `sol_brasil/sol_brasil/doctype/contrato_preliminar`
- `sol_brasil/sol_brasil/doctype/configurações_do_provedor`

Regras:

- Um Lead só pode virar cliente definitivo se possuir contrato preliminar elegível.
- Existem dois fluxos:
  - Pré-pagamento
  - Pós-pagamento
- Pré-pagamento pode exigir confirmação do pagamento antes da conversão.
- Pós-pagamento fica apto após o contrato ser preenchido.
- A configuração permite:
  - deixar o operador escolher o fluxo;
  - usar somente pré-pagamento;
  - usar somente pós-pagamento.
- Ao salvar o Customer completo após a conversão:
  - o contrato preliminar é marcado como convertido;
  - um `Subscription` definitivo é criado;
  - o contrato é vinculado ao cliente;
  - o Lead recebe status `Converted`.

Configurações acessíveis em:

`Configurações → Configurações do provedor`

## Ficha central do cliente

Abas atuais:

- Detalhes
- Endereço e contato
- Provedor
- Contratos
- Financeiro
- Atendimentos
- Configuração financeira
- Fiscal
- Regras comerciais
- Acesso ao portal
- Mais informações
- Relacionamentos

A aba Equipe responsável foi removida/ocultada porque não será usada.

## Aba Provedor

Dividida em duas seções.

### Acesso PPPoE e contrato

- Usuário PPPoE
- Senha PPPoE
- Contrato vinculado (`Subscription`)
- Botão `Consultar ou trocar contrato`
- Situação da conexão
- Plano de internet
- Data de ativação

O botão consulta somente contratos utilizáveis pertencentes ao cliente. O servidor impede:

- contrato pertencente a outro cliente;
- contrato cancelado;
- contrato concluído.

Ao vincular contrato, o plano do cliente é atualizado com o primeiro plano do contrato.

Clientes que já possuíam contrato foram vinculados automaticamente.

### Equipamentos e rede óptica

- Endereço IPv4
- Endereço MAC
- VLAN
- Splitter óptico
- Caixa de atendimento (CTO/NAP)
- OLT
- Slot da OLT
- PON
- Porta PON
- ONU/ONT — número de série
- ID da ONU/ONT
- Modelo da ONU/ONT
- Sinal RX em dBm
- Sinal TX em dBm
- Observações técnicas da rede

Os campos estão definidos em `sol_brasil/install.py` e a interação do contrato em `sol_brasil/public/js/customer.js`.

## Contratos na ficha

- Aba Contratos lista os `Subscription` do cliente.
- Exibe contrato, planos, início, término, situação e mensalidade.
- Permite criar novo contrato.
- O painel é carregado por `sol_brasil/customer_panel.py`.

## Financeiro na ficha

- Lista todas as faturas/boletos em aberto.
- Lista os pagos do ano selecionado.
- Permite trocar o ano do histórico.
- Operações disponíveis:
  - abrir;
  - imprimir;
  - baixar PDF;
  - receber/pagar;
  - criar nova fatura.
- Dados reais vêm de `Sales Invoice` e `Payment Entry`.

## Atendimentos

- Aba Atendimentos lista chamados (`Issue`) e ordens de serviço (`Maintenance Visit`).
- Permite abrir chamado.
- Permite gerar ordem de serviço vinculada ao cliente.
- O painel possui tratamento de erro para não ficar preso em “Carregando atendimentos”.

## Histórico interno e comentários

- Comentários nativos do Frappe ficam vinculados ao documento em `Comment`.
- São usados como histórico interno da equipe.
- Existe botão explícito:
  `Operações do cliente → Registrar comentário interno`.
- O botão também existe em Leads.
- Após registrar, aparece confirmação e a ficha é atualizada.
- Endpoint: `sol_brasil.customer.add_internal_comment`.

## Retorno automático para a ficha

Implementado em:

- `sol_brasil/public/js/related_return.js`
- `sol_brasil/public/js/customer.js`

Aplica-se a:

- Subscription
- Sales Invoice
- Payment Entry
- Issue
- Maintenance Visit
- Asset

Pode ser ativado/desativado em Configurações do Provedor.

## Tradução PT-BR

- Usuário Administrator configurado em `pt-BR`.
- Idioma padrão do sistema definido como `pt-BR`.
- Catálogo próprio em `sol_brasil/locale/pt_BR.po`.
- Foram revisados rótulos e descrições de:
  - clientes;
  - Leads;
  - endereços e contatos;
  - contratos e planos;
  - faturas e recebimentos;
  - chamados e ordens de serviço;
  - equipamentos;
  - configurações e histórico.
- A aba Endereço e contato foi validada visualmente após a correção.
- Não alterar estilos para traduzir; usar catálogo PO, rótulos de Custom Fields ou Property Setters.

## API

O Frappe oferece REST automaticamente:

```text
/api/resource/Customer
/api/resource/Lead
/api/resource/Subscription
/api/resource/Sales Invoice
```

Autenticação por token:

```http
Authorization: token API_KEY:API_SECRET
```

Recomendação arquitetural: expor integrações futuras por endpoints próprios sob:

```text
/api/method/sol_brasil...
```

Isso evita acoplar aplicativos externos aos nomes e estruturas internas do ERPNext.

## Dados de demonstração

Arquivo: `sol_brasil/demo.py`.

Cliente principal:

- `Cliente Demonstração Fibra`
- Plano: `Fibra 500 Mbps - Demonstração`
- Contrato: `ACC-SUB-2026-00001`
- PPPoE: `demo.fibra500`
- Possui faturas, pagamentos, chamado e ordem de serviço fictícios.

O contrato foi validado como vinculado ao cliente de demonstração.

## Arquivos centrais do app

- `sol_brasil/hooks.py`
- `sol_brasil/install.py`
- `sol_brasil/workspace.py`
- `sol_brasil/customer.py`
- `sol_brasil/lead.py`
- `sol_brasil/customer_panel.py`
- `sol_brasil/customer_dashboard.py`
- `sol_brasil/demo.py`
- `sol_brasil/locale/pt_BR.po`
- `sol_brasil/public/js/customer.js`
- `sol_brasil/public/js/customer_list.js`
- `sol_brasil/public/js/customer_quick_entry.js`
- `sol_brasil/public/js/lead.js`
- `sol_brasil/public/js/contrato_preliminar.js`
- `sol_brasil/public/js/related_return.js`

## Cuidados técnicos

- O app `sol_brasil` possui várias mudanças locais ainda não consolidadas em commit.
- Não apagar ou sobrescrever arquivos não relacionados.
- Usar `apply_patch` nas alterações manuais.
- Depois de mudar hooks, campos ou Python, limpar cache e, quando necessário, reiniciar somente o serviço Frappe.
- Depois de mudar traduções, executar `bench build --app sol_brasil`.
- Validar mudanças visuais diretamente no navegador.
- Não alterar o design global sem solicitação explícita.
- O DocType `Configurações do Provedor` usa nome acentuado; a pasta e os arquivos internos também mantêm os acentos exigidos pelo Frappe.

## Planejamento recomendado

### Prioridade 1 — Estruturar a rede como cadastros próprios

Hoje OLT, PON, CTO e ONU são campos textuais na ficha. Para uma operação real, criar DocTypes relacionados:

- POP
- OLT
- Placa/slot da OLT
- Porta PON
- CTO/NAP
- Porta da CTO
- ONU/ONT
- Concentrador/BNG
- Pool de IP
- VLAN

Depois substituir gradualmente campos de texto por Links. Isso permitirá ocupação de portas, disponibilidade, mapas, inventário e prevenção de duplicidade.

### Prioridade 2 — Autenticação e integração de rede

- Criar entidade de acesso PPPoE independente, vinculada ao contrato e cliente.
- Preparar integração com RADIUS/FreeRADIUS.
- Preparar integração com MikroTik, Huawei, ZTE e outros fabricantes.
- Sincronizar bloqueio, desbloqueio e troca de plano.
- Registrar logs de autenticação e última conexão.
- Nunca expor senha PPPoE em listagens ou logs.

### Prioridade 3 — Contrato próprio do provedor

O `Subscription` atende à recorrência, mas ainda possui terminologia e regras genéricas. Planejar um contrato de serviço próprio ou uma camada de domínio sobre Subscription com:

- número do contrato;
- titular;
- endereço de instalação;
- plano;
- fidelidade;
- vencimento;
- forma de cobrança;
- taxa de instalação;
- equipamentos em comodato;
- aceite e assinatura;
- suspensão e cancelamento;
- histórico de alterações.

### Prioridade 4 — Cobrança brasileira

- Integração com banco ou gateway.
- Pix e boleto registrado.
- Linha digitável, código de barras e QR Code.
- Webhook de pagamento.
- Baixa automática.
- Régua de cobrança.
- Multa, juros e desconto.
- Remessa/retorno quando aplicável.
- Nota fiscal de comunicação conforme definição fiscal/contábil.

### Prioridade 5 — Ordens de serviço

- Criar tipos próprios: instalação, reparo, retirada, troca de equipamento e visita técnica.
- Agenda e técnico responsável.
- SLA e prioridade.
- Checklist.
- Fotos e anexos.
- Assinatura do cliente.
- Materiais utilizados e baixa de estoque.
- Medição óptica antes/depois.
- Conclusão da OS atualizando contrato e equipamentos.

### Prioridade 6 — Portal e aplicativo do cliente

- Segunda via de fatura/boleto.
- Pix copia e cola.
- Contratos e documentos.
- Abertura e acompanhamento de chamados.
- Desbloqueio por confiança, se adotado.
- Atualização de dados cadastrais.
- Notificações.

### Prioridade 7 — Segurança e permissões

- Criar papéis próprios: atendimento, financeiro, técnico, supervisor e administrador.
- Restringir CPF/CNPJ, senha PPPoE e dados financeiros.
- Registrar auditoria de alterações sensíveis.
- Separar permissões de visualizar e revelar senhas.
- Criar usuário de API com permissões mínimas para cada integração.

### Prioridade 8 — Qualidade e manutenção

- Criar testes automatizados para CPF/CNPJ, conversão de Lead, contrato e retorno de navegação.
- Criar testes de API.
- Versionar migrações e fixtures.
- Consolidar mudanças em commits pequenos e documentados.
- Planejar atualização futura do Frappe/ERPNext sem alterar diretamente o core.

## Próxima tarefa sugerida

Começar pela modelagem dos cadastros de rede, nesta ordem:

1. POP
2. OLT
3. Slot/placa
4. Porta PON
5. CTO/NAP e portas
6. ONU/ONT

Em seguida, trocar os campos textuais da ficha do cliente por Links para essas entidades, preservando os dados já cadastrados e mantendo uma migração compatível.

