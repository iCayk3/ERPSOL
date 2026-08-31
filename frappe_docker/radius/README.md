# Operação RADIUS PPPoE

Esta pasta contém a base operacional isolada do ERP. O FreeRADIUS consulta apenas o banco `radius`; o ERP projeta contratos por uma fila persistente e nunca participa da autenticação em tempo real.

## Inicialização

No ambiente de desenvolvimento padrão, o caminho recomendado é executar, na raiz do repositório:

`powershell -ExecutionPolicy Bypass -File .\frappe_docker\radius\bootstrap-development.ps1`

O script localiza o Docker Desktop no PATH ou no perfil do usuário, gera segredos locais, sobe primário/secundário e banco, configura o site e executa a primeira reconciliação. Use as etapas manuais abaixo quando precisar controlar cada ação separadamente.

1. Copie `.env.example` para um arquivo de ambiente fora do Git e troque todos os segredos.
   Ajuste `ERP_DOCKER_NETWORK` para a rede Docker do bench (`devcontainer-example_default` no desenvolvimento atual).
2. Inicie a base e o primário:

   `docker compose --env-file radius/.env -f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.radius.yaml up -d --build radius-db radius-primary`

3. Configure cada site Frappe, sem registrar a senha no repositório:

   `bench --site SITE set-config radius_db_host radius-db`
   `bench --site SITE set-config radius_db_port 3306`
   `bench --site SITE set-config radius_db_name radius`
   `bench --site SITE set-config radius_db_user radius_app`
   `bench --site SITE set-config radius_db_password 'SEGREDO'`

4. Execute `bench --site SITE migrate`, sincronize os NAS e reprovisione os contratos:

   `bench --site SITE execute sol_brasil.radius_provisioning.synchronize_nas`
   `bench --site SITE execute sol_brasil.radius_provisioning.reconcile_radius`
   `bench --site SITE execute sol_brasil.radius_provisioning.process_pending_events`

O usuário SQL do ERP deve ter somente `SELECT`, `INSERT`, `UPDATE` e `DELETE` no schema operacional. O root é usado apenas pelo container na criação inicial.

## Validação e operação

- Rode `validate-lab.ps1` para Access-Accept, Access-Reject e accounting Start/Interim/Stop.
- Cadastre cada MikroTik em **NAS RADIUS** e restrinja `RADIUS_LAB_NETWORK` à rede do laboratório.
- Configure `/ppp aaa set use-radius=yes accounting=yes interim-update=5m` e os servidores com portas 1812/1813.
- O contrato mostra o estado da fila e oferece **RADIUS > Sessões e consumo**.
- Bloqueio, suspensão e cancelamento retiram `radcheck`/`radreply`; uma sessão existente recebe Disconnect quando o NAS suporta CoA.
- Mudanças são idempotentes por contrato e versão. Erros repetem com backoff até dez tentativas.

## Modo sombra, piloto e produção

Use [RUNBOOK_ROLLOUT.md](runbooks/RUNBOOK_ROLLOUT.md). O secundário local pode ser ensaiado com o profile `radius-ha`:

`docker compose --profile radius-ha --env-file radius/.env -f compose.yaml -f overrides/compose.radius.yaml up -d --build`

Em produção, primário e secundário devem estar em hosts ou zonas diferentes. O profile local comprova configuração reproduzível, mas não substitui diversidade física nem banco com recuperação testada.
