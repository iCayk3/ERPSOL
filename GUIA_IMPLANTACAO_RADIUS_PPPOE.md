# Guia de implantação do RADIUS para autenticação PPPoE

## Objetivo

Implantar autenticação, autorização e accounting PPPoE no produto SOL Provedor sem tornar o acesso dos assinantes dependente da disponibilidade do ERPNext.

A arquitetura adotada deve manter:

- o ERPNext/SOL Brasil como fonte de verdade para clientes, contratos, planos, cobrança e situação do serviço;
- o FreeRADIUS como responsável pela autenticação em tempo real;
- uma base operacional própria para contas, perfis, NAS e sessões RADIUS;
- sincronização assíncrona e idempotente entre o ERP e o RADIUS;
- suporte a CoA/Disconnect para aplicar alterações em conexões já estabelecidas.

## Arquitetura de referência

```text
ERPNext / SOL Brasil
  clientes, contratos, planos e financeiro
                    |
                    | eventos de provisionamento
                    v
          Base operacional RADIUS
  contas, perfis, atributos, NAS e accounting
                    |
                    v
          FreeRADIUS primário/secundário
                    |
        Access / Accounting / CoA-Disconnect
                    v
       MikroTik / BNG / concentrador PPPoE
                    |
                    v
              Assinante PPPoE
```

## Princípios da implantação

1. O Frappe não deve responder diretamente ao protocolo RADIUS.
2. O FreeRADIUS não deve consultar o ERP por HTTP durante cada autenticação.
3. Uma indisponibilidade temporária do ERP não deve derrubar nem impedir acessos já provisionados.
4. Alterações devem ser enviadas por eventos persistentes, com repetição automática em caso de falha.
5. As credenciais nunca devem aparecer em logs, mensagens de erro ou histórico de eventos.
6. Contrato, situação financeira, provisionamento e estado da conexão são estados distintos.

> **Decisão de produto atualizada em 25/08/2026:** o sistema utiliza somente os campos PPPoE da ficha do cliente. `Perfil RADIUS` e a tabela separada `Acesso PPPoE` não fazem parte da interface operacional. Velocidade, sessões, pools, filtros, accounting e atributos adicionais ficam diretamente no `Plano de internet` (`Subscription Plan`). As descrições abaixo que mencionam esses DocTypes representam o desenho inicial e ficam preservadas apenas como histórico arquitetural.

---

## Passo 1 — Criar os modelos de gestão RADIUS no ERP

**Situação:** concluído no ambiente de desenvolvimento em 25/08/2026.

### Objetivo

Representar acessos, perfis e concentradores como entidades próprias do provedor, permitindo mais de um acesso por cliente ou contrato.

### Implementação

Criar no app `sol_brasil` os seguintes DocTypes:

#### Acesso PPPoE

Campos mínimos:

- cliente;
- contrato (`Subscription`);
- plano e perfil RADIUS;
- usuário PPPoE único;
- senha protegida;
- situação do acesso;
- estado do provisionamento;
- IPv4 fixo opcional;
- pool IPv4;
- prefixo ou pool IPv6;
- MAC autorizado opcional;
- limite de sessões simultâneas;
- NAS ou grupo de NAS permitido;
- última sincronização;
- última autenticação;
- mensagem do último erro de provisionamento.

#### Perfil RADIUS

Campos mínimos:

- nome e código imutável do perfil;
- vínculo com `Subscription Plan`;
- download e upload;
- expressão `Mikrotik-Rate-Limit` gerada;
- pool IPv4 e parâmetros IPv6;
- limite de sessões;
- intervalo de accounting;
- filtros e atributos adicionais;
- indicação de perfil normal ou perfil de bloqueio.

#### NAS RADIUS

Campos mínimos:

- nome;
- endereço IP;
- `NAS-Identifier` esperado;
- fabricante;
- segredo compartilhado protegido;
- porta de CoA/Disconnect;
- suporte a CoA;
- ativo/inativo.

#### Evento de Provisionamento RADIUS

Campos mínimos:

- tipo da operação;
- acesso relacionado;
- versão do objeto;
- conteúdo sem dados secretos expostos;
- estado: Pendente, Processando, Concluído ou Erro;
- número de tentativas;
- próxima tentativa;
- mensagem de erro sanitizada.

### Regras importantes

- O usuário PPPoE deve possuir índice único e comparação sem ambiguidade de maiúsculas/minúsculas.
- Um acesso não pode apontar para contrato de outro cliente.
- O perfil precisa estar ativo para ser atribuído.
- A senha deve usar campo protegido e nunca ser devolvida em listagens ou APIs comuns.
- Toda alteração relevante deve gerar evento de provisionamento na mesma transação lógica.

### Critério de conclusão

É possível cadastrar dois acessos para o mesmo cliente, associá-los a contratos diferentes e visualizar seu estado na ficha central do cliente.

### Implementação realizada — desenho vigente

- Os campos PPPoE existentes na ficha do cliente foram mantidos como fonte única.
- A tabela duplicada de acessos e o campo explícito de Perfil RADIUS foram removidos da interface.
- Download, upload, sessões, accounting, pools, filtros e atributos RADIUS foram adicionados diretamente ao Plano de internet.
- `Mikrotik-Rate-Limit` é gerado automaticamente pelo plano.
- Senha PPPoE e segredo do NAS armazenados em campos `Password`.
- Atributos adicionais do plano são validados e não aceitam chaves de senha ou segredo.
- `NAS RADIUS` permanece disponível no workspace Rede e equipamentos.
- Migração de schema e testes de fumaça executados no site `development.localhost`.

O processamento dos eventos e sua escrita no banco operacional do FreeRADIUS continuam reservados ao Passo 4.

---

## Passo 2 — Migrar os dados PPPoE existentes

### Objetivo

Converter os campos PPPoE atualmente gravados diretamente em `Customer` para registros de `Acesso PPPoE`, sem perder dados.

### Preparação

- Identificar clientes com usuário PPPoE preenchido.
- Detectar usuários duplicados antes da migração.
- Verificar contratos inexistentes, cancelados ou pertencentes a outro cliente.
- Gerar relatório de inconsistências e corrigi-las antes da ativação.

### Migração

Para cada cliente com credenciais existentes:

1. criar um `Acesso PPPoE`;
2. vincular o contrato já selecionado no cliente;
3. derivar o perfil a partir do plano do contrato;
4. copiar IP, MAC, VLAN e demais dados aplicáveis;
5. preservar a senha utilizando acesso controlado ao campo protegido;
6. marcar o registro como `Pendente de provisionamento`;
7. registrar que a origem foi a migração dos campos do cliente.

Os campos antigos devem permanecer temporariamente somente para compatibilidade e leitura. Sua remoção deve ocorrer em uma migração posterior, depois da validação em produção.

### Segurança e retorno

- Executar backup antes da migração.
- Tornar o patch idempotente para que possa ser executado novamente.
- Não apagar campos antigos na primeira versão.
- Produzir totais de lidos, migrados, ignorados e inconsistentes.

### Critério de conclusão

Todos os usuários PPPoE válidos aparecem como `Acesso PPPoE`, sem duplicidades e com cliente, contrato e perfil corretos.

---

## Passo 3 — Subir FreeRADIUS e banco operacional no desenvolvimento

### Objetivo

Disponibilizar um ambiente isolado para autenticação e accounting, sem usar diretamente as tabelas internas do ERPNext.

### Componentes

- um container FreeRADIUS;
- um banco SQL operacional RADIUS;
- schema oficial compatível com a versão adotada do FreeRADIUS;
- volumes persistentes para configuração;
- healthcheck do serviço e do banco;
- rede Docker acessível pelo ambiente Frappe e pelo MikroTik de laboratório.

### Configuração inicial

- Habilitar autenticação SQL.
- Habilitar accounting SQL.
- Instalar o dicionário do fabricante dos concentradores utilizados.
- Cadastrar somente NAS de laboratório.
- Restringir UDP 1812 e 1813 aos endereços autorizados.
- Preparar a recepção e o envio de CoA/Disconnect.
- Desabilitar logs que revelem senhas ou conteúdo sensível.

### Banco

Mesmo que inicialmente utilize a mesma instância de MariaDB do ambiente, a base deve possuir:

- database/schema separado;
- usuário SQL próprio;
- privilégios mínimos;
- política de backup própria;
- possibilidade de separação física futura sem alterar o ERP.

### Critério de conclusão

Um teste local controlado recebe `Access-Accept` para uma credencial válida, `Access-Reject` para uma inválida e grava Start/Interim/Stop no accounting.

---

## Passo 4 — Implementar a sincronização ERP → RADIUS

### Objetivo

Provisionar contas e perfis no banco operacional sem consultas síncronas ao ERP durante o login PPPoE.

### Fluxo

1. Uma alteração no ERP cria um `Evento de Provisionamento RADIUS`.
2. Um worker do Frappe seleciona eventos pendentes.
3. O worker valida o estado atual do acesso e do contrato.
4. A operação é aplicada ao banco RADIUS por `upsert` ou transação equivalente.
5. O resultado e a versão sincronizada são registrados no acesso.
6. Falhas transitórias são repetidas com espera progressiva.
7. Falhas definitivas ficam visíveis para ação operacional.

### Eventos mínimos

- criar acesso;
- atualizar credencial;
- trocar perfil;
- alterar IP ou pool;
- habilitar;
- bloquear;
- desbloquear;
- suspender;
- cancelar;
- remover acesso somente após política de retenção.

### Idempotência

Cada evento deve possuir identificador e versão. Processar o mesmo evento mais de uma vez não pode criar registros duplicados nem reverter uma alteração mais recente.

### Observabilidade

Criar indicadores para:

- eventos pendentes;
- eventos com erro;
- tempo médio de provisionamento;
- acessos divergentes entre ERP e RADIUS;
- data da última sincronização bem-sucedida.

### Critério de conclusão

Criar, alterar plano, trocar senha, bloquear e desbloquear um acesso no ERP produz o estado correspondente no RADIUS, inclusive após simular falha e repetição do worker.

---

## Passo 5 — Validar com um MikroTik de laboratório

### Objetivo

Comprovar o ciclo completo utilizando um concentrador real ou CHR dedicado ao laboratório.

### Cenários obrigatórios

- autenticação com usuário e senha válidos;
- rejeição de senha incorreta;
- usuário inexistente;
- acesso suspenso ou cancelado;
- aplicação do perfil de velocidade;
- atribuição por pool;
- atribuição de IP fixo;
- limite de sessões simultâneas;
- restrição por NAS, quando configurada;
- restrição por MAC, quando configurada;
- envio de Start;
- envio periódico de Interim-Update;
- envio de Stop;
- contagem de upload e download;
- troca de plano por CoA quando suportada;
- Disconnect e nova autenticação;
- recuperação após indisponibilidade temporária de um servidor.

### Configuração sugerida

- habilitar RADIUS em `/ppp aaa`;
- configurar accounting;
- usar intervalo inicial de Interim-Update de cinco minutos;
- cadastrar o servidor RADIUS primário e, quando disponível, o secundário;
- habilitar recebimento de Disconnect/CoA apenas de origem confiável;
- manter um usuário local de emergência que não conflite com usuários RADIUS.

### Evidências

Registrar para cada teste:

- data e responsável;
- usuário de teste;
- resultado esperado;
- resultado observado;
- atributos enviados e recebidos sem segredos;
- sessão correspondente no accounting;
- capturas ou logs sanitizados quando necessário.

### Critério de conclusão

Todos os cenários obrigatórios foram aprovados, e os valores de velocidade, endereço, sessão e consumo coincidem entre MikroTik, FreeRADIUS e painel do ERP.

---

## Passo 6 — Executar em modo sombra

### Objetivo

Observar o comportamento real antes de transferir ao novo RADIUS o controle de autenticação dos assinantes.

### Estratégia

- Manter a autenticação atual em produção.
- Provisionar cópias controladas das contas no novo RADIUS.
- Receber accounting de um concentrador ou grupo de teste, quando a topologia permitir.
- Comparar usuários, sessões, IPs, tráfego e estados.
- Não aplicar bloqueios financeiros automáticos nessa fase.
- Não desconectar sessões de clientes fora do grupo autorizado.

### Validações

- nenhuma credencial faltante;
- nenhum usuário duplicado;
- planos convertidos para atributos corretos;
- accounting sem crescimento anormal ou sessões presas;
- relógios sincronizados por NTP;
- filas de sincronização sem acúmulo;
- alertas e dashboards operacionais funcionando.

### Duração recomendada

Manter o modo sombra por pelo menos um ciclo operacional representativo, incluindo ativações, troca de plano, atraso, pagamento, suspensão e cancelamento.

### Critério de conclusão

Não existem divergências críticas, a sincronização permanece estável e a equipe consegue diagnosticar uma autenticação usando ERP, logs RADIUS e dados do NAS.

---

## Passo 7 — Migrar um pequeno grupo de assinantes

### Objetivo

Colocar o novo RADIUS no caminho de autenticação real com impacto limitado e retorno rápido.

### Seleção do piloto

Escolher um grupo que tenha:

- um único concentrador ou área facilmente isolável;
- diversidade de planos;
- alguns IPs fixos e dinâmicos;
- clientes internos ou colaboradores, quando possível;
- janela de mudança e equipe de suporte disponível.

Evitar começar por clientes críticos, corporativos ou com configurações excepcionais.

### Execução

1. confirmar backup e plano de retorno;
2. congelar alterações manuais durante a janela;
3. reconciliar ERP e banco RADIUS;
4. apontar o NAS piloto para o novo serviço;
5. desconectar apenas as sessões do grupo piloto, se necessário;
6. acompanhar autenticação, velocidade, IP e accounting;
7. testar bloqueio e desbloqueio com contas preparadas;
8. manter suporte reforçado durante a observação.

### Retorno

O retorno deve consistir em restaurar no NAS piloto a configuração anterior de autenticação. Nenhum rollback pode depender da exclusão dos dados coletados pelo novo RADIUS.

### Critério de conclusão

O grupo piloto opera durante o período acordado sem incidentes críticos, e os incidentes menores possuem causa conhecida e correção validada.

---

## Passo 8 — Adicionar redundância e ampliar a migração

### Objetivo

Eliminar pontos únicos de falha antes de adotar o serviço para toda a base.

### Arquitetura de produção

- dois servidores FreeRADIUS em hosts ou zonas diferentes;
- ambos configurados nos NAS como primário e secundário;
- configuração versionada e reproduzível;
- banco operacional altamente disponível ou com recuperação testada;
- monitoramento de autenticação, accounting, banco e filas;
- backups e restauração periodicamente testados;
- rede privada, VPN ou RadSec quando houver travessia de rede não confiável.

### Testes de falha

- desligar o RADIUS primário e autenticar pelo secundário;
- restaurar o primário sem interromper sessões;
- interromper temporariamente o banco;
- verificar comportamento do accounting durante a falha;
- testar repetição dos eventos do ERP;
- simular perda de Stop e reconciliar sessões antigas;
- testar recuperação a partir de backup.

### Expansão

Migrar em lotes identificáveis por NAS, região ou grupo de clientes. Para cada lote:

1. reconciliar dados;
2. registrar janela e responsáveis;
3. executar testes de fumaça;
4. observar indicadores;
5. aprovar continuidade ou retornar;
6. documentar ocorrências e ajustes.

### Critério de conclusão

Todos os NAS utilizam os dois servidores, os procedimentos de contingência foram testados e a base completa opera pelo novo RADIUS dentro dos indicadores definidos.

---

## Política de bloqueio sugerida

| Situação no ERP | Comportamento RADIUS |
|---|---|
| Ativo | Aceitar com o perfil contratado |
| Em carência | Aceitar normalmente e sinalizar no ERP |
| Bloqueado financeiramente | Aplicar perfil reduzido ou walled garden |
| Suspenso tecnicamente | Rejeitar e desconectar sessão existente |
| Cancelado | Rejeitar e desconectar sessão existente |
| Provisionamento pendente | Não declarar o acesso operacional |
| Erro de sincronização | Alertar a operação e preservar o último estado conhecido |

Mudanças de velocidade e filtros podem ser aplicadas por CoA quando suportadas. Mudanças de IP, pool ou rota devem provocar Disconnect para que os novos atributos sejam recebidos na autenticação seguinte.

## Checklist final de aceite

- [x] DocTypes e permissões implantados.
- [ ] Migração de dados reconciliada.
- [ ] FreeRADIUS e banco operacional documentados e reproduzíveis.
- [ ] Sincronização idempotente testada.
- [ ] Credenciais ausentes de logs e auditorias comuns.
- [ ] Accounting Start, Interim e Stop validado.
- [ ] CoA e Disconnect validados.
- [ ] Perfil de bloqueio financeiro validado.
- [ ] Monitoramento e alertas ativos.
- [ ] Servidores primário e secundário testados.
- [ ] Backup e restauração testados.
- [ ] Plano de retorno executado em laboratório.
- [ ] Piloto aprovado.
- [ ] Migração total aprovada pela operação.

## Próximo passo

Iniciar pelo desenho dos quatro DocTypes do Passo 1 e definir os atributos RADIUS que cada plano de internet deverá produzir. Nenhum cliente deve ser migrado antes de o modelo de estados, a política de bloqueio e a estratégia de senha estarem formalmente definidos.
